// Pure helpers: number formatting, plain-English summaries of the API data and error messages.
// No DOM access here, so `node --test tests/web` can check them. Nothing in this file invents data:
// every sentence is derived from the API response, and missing values become "—" or are skipped.

export const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
  "September", "October", "November", "December"];
export const MONTH_ABBR = MONTHS.map((m) => m.slice(0, 3));

/** A finite number, or null for null / undefined / NaN / strings. */
export function num(value) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

/** "57 mm", "0.4 days"… or "—" when the value is missing. Minus sign is the typographic one. */
export function fmt(value, digits = 0, unit = "") {
  const n = num(value);
  if (n === null) return "—";
  const text = n.toFixed(digits).replace("-", "−");
  return unit ? `${text} ${unit}` : text;
}

/** HTML-escape any text that comes from data before it goes into markup. */
export function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

/** Months (1–12) → consecutive runs, wrapping over New Year: [11,12,1,5] → [[11,1],[5,5]]. */
export function monthRuns(months) {
  const set = new Set(months);
  if (set.size === 0) return [];
  if (set.size === 12) return [[1, 12]];
  const runs = [];
  for (let m = 1; m <= 12; m++) {
    const prev = m === 1 ? 12 : m - 1;
    if (!set.has(m) || set.has(prev)) continue; // not the start of a run
    let end = m;
    while (set.has(end === 12 ? 1 : end + 1)) end = end === 12 ? 1 : end + 1;
    runs.push([m, end]);
  }
  return runs;
}

/** [[10,3],[6,6]] → "October–March and June". */
export function formatRuns(runs) {
  const parts = runs.map(([a, b]) => (a === b ? MONTHS[a - 1] : `${MONTHS[a - 1]}–${MONTHS[b - 1]}`));
  if (parts.length <= 1) return parts[0] || "";
  return `${parts.slice(0, -1).join(", ")} and ${parts.at(-1)}`;
}

function byMonth(profile) {
  const out = new Map();
  for (const m of profile?.months || []) if (m && m.month >= 1 && m.month <= 12) out.set(m.month, m);
  return out;
}

/** True when MODIS greenness is missing for every month (MODIS failed or timed out). */
export function ndviMissing(profile) {
  const months = profile?.months || [];
  return months.length > 0 && months.every((m) => num(m.ndvi) === null);
}

/**
 * Plain-English key facts from Shape 1: [{icon, text}]. A fact is skipped when its data is missing.
 * Thresholds are the ones in docs/indicators.md (I-05 frost, I-06 heat > 35 °C, I-09 bare).
 */
export function keyFacts(profile) {
  const months = byMonth(profile);
  if (months.size < 12) return [];
  const facts = [];
  const all = [...months.values()];
  const val = (field) => all.map((m) => num(m[field]));

  const rain = val("rain_mm");
  if (rain.every((v) => v !== null)) {
    const total = rain.reduce((a, b) => a + b, 0);
    // Wettest months that together bring at least 60 % of the year's rain.
    const order = all.map((m) => m.month).sort((a, b) => months.get(b).rain_mm - months.get(a).rain_mm);
    const wet = [];
    let acc = 0;
    for (const m of order) {
      if (total > 0 && acc / total >= 0.6) break;
      wet.push(m);
      acc += months.get(m).rain_mm;
    }
    if (total > 0) {
      facts.push({ icon: "🌧️", text: `About ${fmt(total, 0, "mm")} of rain a year. Most of it falls in ${formatRuns(monthRuns(wet))}.` });
    }
  }

  const balance = all.filter((m) => num(m.water_balance_mm) !== null);
  if (balance.length === 12) {
    const dry = balance.filter((m) => m.water_balance_mm < 0).map((m) => m.month);
    if (dry.length) {
      const worst = balance.reduce((a, b) => (b.water_balance_mm < a.water_balance_mm ? b : a));
      facts.push({
        icon: "💧",
        text: `Rain is less than the water the air takes from the field in ${formatRuns(monthRuns(dry))}. ` +
          `Worst in ${MONTHS[worst.month - 1]} (${fmt(worst.water_balance_mm, 0, "mm")}).`,
      });
    } else {
      facts.push({ icon: "💧", text: "Rain is more than the water the air takes from the field in every month." });
    }
  }

  if (!ndviMissing(profile)) {
    const bare = all.filter((m) => m.likely_bare === true).map((m) => m.month);
    facts.push(bare.length
      ? { icon: "🟫", text: `The field was probably bare in ${formatRuns(monthRuns(bare))} (satellite greenness, 2024–2025).` }
      : { icon: "🌿", text: "The field looked covered by plants all year (satellite greenness, 2024–2025)." });
  }

  const heat = val("heat_days");
  if (heat.every((v) => v !== null)) {
    const total = heat.reduce((a, b) => a + b, 0);
    const hot = all.filter((m) => m.heat_days >= 1).map((m) => m.month);
    facts.push(total < 0.5
      ? { icon: "🔥", text: "Very hot days (over 35 °C) are rare here." }
      : { icon: "🔥", text: `About ${fmt(total, 0)} very hot days (over 35 °C) a year${hot.length ? `, mostly in ${formatRuns(monthRuns(hot))}` : ""}.` });
  }

  const frost = val("frost_days");
  if (frost.every((v) => v !== null)) {
    const total = frost.reduce((a, b) => a + b, 0);
    const cold = all.filter((m) => m.frost_days >= 1).map((m) => m.month);
    facts.push(total < 0.5
      ? { icon: "❄️", text: "Frost is rare here." }
      : { icon: "❄️", text: `About ${fmt(total, 0)} frost days a year${cold.length ? `, mostly in ${formatRuns(monthRuns(cold))}` : ""}.` });
  }
  return facts;
}

/** Trend sentences (I-10, I-11) or [] when the values are missing. */
export function trendFacts(trends) {
  const out = [];
  const base = trends?.baseline || "2005-2014";
  const baseText = base.replace("-", "–");
  const rain = num(trends?.rain_change_pct);
  if (rain !== null) {
    const text = Math.abs(rain) < 2 ? `It rains about the same as in ${baseText}.`
      : rain < 0 ? `It rains about ${fmt(-rain, 0)}% less than in ${baseText}.`
        : `It rains about ${fmt(rain, 0)}% more than in ${baseText}.`;
    out.push({ icon: rain <= -2 ? "🔻" : rain >= 2 ? "🔺" : "➖", text });
  }
  const heat = num(trends?.heat_days_change);
  if (heat !== null) {
    const text = Math.abs(heat) < 0.5 ? `About the same number of very hot days as in ${baseText}.`
      : heat > 0 ? `About ${fmt(heat, 0)} more very hot days a year than in ${baseText}.`
        : `About ${fmt(-heat, 0)} fewer very hot days a year than in ${baseText}.`;
    out.push({ icon: heat >= 0.5 ? "🔺" : heat <= -0.5 ? "🔻" : "➖", text });
  }
  return out;
}

export const LEVEL_TEXT = { good: "Good", neutral: "Fair", poor: "Poor" };

/** Level word for a 0–100 score, from the API label (rotations.label) or the same thresholds. */
export function levelText(label, score) {
  if (LEVEL_TEXT[label]) return LEVEL_TEXT[label];
  const n = num(score);
  if (n === null) return "Not available";
  return n >= 67 ? "Good" : n >= 34 ? "Fair" : "Poor";
}

/** Readable crop name: from the API catalogue, else "durum_wheat" → "Durum wheat". */
export function cropName(id, names) {
  if (names && names[id]) return names[id];
  const text = String(id ?? "").replace(/_/g, " ").trim();
  return text ? text[0].toUpperCase() + text.slice(1) : "Unknown crop";
}

/**
 * Plain-English message for a failed request. `kind` comes from api.js:
 * offline | timeout | network | validation | not_found | nasa | server.
 */
export function errorMessage(kind, { freePoint = false } = {}) {
  switch (kind) {
    case "offline":
      return {
        title: "You're offline",
        text: freePoint
          ? "A new point on the map needs an internet connection to fetch NASA data. Connect and try again, or pick a demo field."
          : "Only results you opened before on this phone work offline. Connect to the internet, or go back to the answers you used last time.",
      };
    case "timeout":
      return {
        title: "NASA data is taking too long",
        text: "We are still fetching data for this point. Try again in a minute — it is usually ready by then. You can also try a demo field.",
      };
    case "nasa":
      return {
        title: "We couldn't reach NASA data right now",
        text: "Try a demo field, or try again in a minute.",
      };
    case "validation":
      return {
        title: "Some answers could not be used",
        text: "Check the crops in your rotation and try again.",
      };
    case "not_found":
      return {
        title: "This field is not available any more",
        text: "Pick another field and try again.",
      };
    case "network":
      return {
        title: "We couldn't reach FarmLens",
        text: "The connection dropped. Check your signal and try again.",
      };
    default:
      return {
        title: "Something went wrong on our side",
        text: "Try again in a minute. If it keeps happening, try a demo field.",
      };
  }
}

/** HTTP status → error kind (see errorMessage). */
export function errorKind(status) {
  if (status === 422 || status === 400) return "validation";
  if (status === 404) return "not_found";
  if (status === 503 || status === 502 || status === 504) return "nasa";
  return "server";
}

/**
 * Synthetic cache key for a POST /api/analyze body (sw.js keeps the last answer per key for offline use):
 * keys sorted at every level, numbers as numbers, rotation order kept, coordinates to 2 decimals.
 */
export function analysisKey(inputs) {
  const norm = (v) => {
    if (Array.isArray(v)) return v.map(norm);
    if (v && typeof v === "object") return Object.fromEntries(Object.keys(v).sort().filter((k) => v[k] !== undefined).map((k) => [k, norm(v[k])]));
    if (typeof v === "string" && v.trim() !== "" && !Number.isNaN(Number(v))) return Number(v);
    return v;
  };
  const body = norm(inputs || {});
  for (const k of ["lat", "lon"]) if (typeof body[k] === "number") body[k] = Math.round(body[k] * 100) / 100;
  return JSON.stringify(body);
}

/** "14 November 2026, 15:42" in the phone's locale-independent English form. */
export function formatDate(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}, ${hh}:${mm}`;
}

/** Lower case, no accents, single spaces: "  Maíz " → "maiz". */
export function normalizeText(text) {
  return String(text ?? "").normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[_\s]+/g, " ").trim();
}

/**
 * Crop id for what the farmer typed in a crop text field, or null.
 * Exact name or id first (case and accents ignored); otherwise the only crop whose name starts with,
 * or else contains, the text ("sunfl" → sunflower). Ambiguous or unknown text → null.
 */
export function findCrop(text, crops) {
  const q = normalizeText(text);
  if (!q) return null;
  const exact = crops.find((c) => normalizeText(c.name) === q || normalizeText(c.id) === q);
  if (exact) return exact.id;
  for (const test of [(n) => n.startsWith(q), (n) => n.includes(q)]) {
    const hits = crops.filter((c) => test(normalizeText(c.name)));
    if (hits.length === 1) return hits[0].id;
    if (hits.length > 1) return null;
  }
  return null;
}
