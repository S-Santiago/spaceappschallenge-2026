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

/** Months (1–12) -> consecutive runs, wrapping over New Year: [11,12,1,5] -> [[11,1],[5,5]]. */
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

/** [[10,3],[6,6]] -> "October–March and June". */
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
 * Plain-English key facts from Shape 1: [{icon, text}], icon = an icon name from icons.js. A fact is skipped when its data is missing.
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
      facts.push({ icon: "rain", text: `About ${fmt(total, 0, "mm")} of rain a year. Most of it falls in ${formatRuns(monthRuns(wet))}.` });
    }
  }

  const balance = all.filter((m) => num(m.water_balance_mm) !== null);
  if (balance.length === 12) {
    const dry = balance.filter((m) => m.water_balance_mm < 0).map((m) => m.month);
    if (dry.length) {
      const worst = balance.reduce((a, b) => (b.water_balance_mm < a.water_balance_mm ? b : a));
      facts.push({
        icon: "drop",
        text: `In ${formatRuns(monthRuns(dry))}, rain is less than the water the field loses. ` +
          `Worst: ${MONTHS[worst.month - 1]} (${fmt(worst.water_balance_mm, 0, "mm")} a month).`,
      });
    } else {
      facts.push({ icon: "drop", text: "Every month, rain is more than the water the field loses." });
    }
  }

  if (!ndviMissing(profile)) {
    const bare = all.filter((m) => m.likely_bare === true).map((m) => m.month);
    facts.push(bare.length
      ? { icon: "bare", text: `Satellite photos show the field was probably bare in ${formatRuns(monthRuns(bare))} (2024–2025 only).` }
      : { icon: "leaf", text: "Satellite photos show the field covered by plants all year (2024–2025 only)." });
  }

  const heat = val("heat_days");
  if (heat.every((v) => v !== null)) {
    const total = heat.reduce((a, b) => a + b, 0);
    const hot = all.filter((m) => m.heat_days >= 1).map((m) => m.month);
    facts.push(total < 0.5
      ? { icon: "sun", text: "Very hot days (over 35 °C) are rare here." }
      : { icon: "sun", text: `About ${fmt(total, 0)} very hot days (over 35 °C) a year${hot.length ? `, mostly in ${formatRuns(monthRuns(hot))}` : ""}.` });
  }

  const frost = val("frost_days");
  if (frost.every((v) => v !== null)) {
    const total = frost.reduce((a, b) => a + b, 0);
    const cold = all.filter((m) => m.frost_days >= 1).map((m) => m.month);
    facts.push(total < 0.5
      ? { icon: "frost", text: "Frost is rare here." }
      : { icon: "frost", text: `About ${fmt(total, 0)} frost days a year${cold.length ? `, mostly in ${formatRuns(monthRuns(cold))}` : ""}.` });
  }
  return facts;
}

/** Trend sentences (I-10, I-11) or [] when the values are missing. `icon` is an icon name (icons.js). */
export function trendFacts(trends) {
  const out = [];
  const base = trends?.baseline || "2005-2014";
  const baseText = base.replace("-", "–");
  const since = /^(\d{4})/.exec(String(trends?.recent ?? ""))?.[1] || "2016"; // recent period: 2016-2025
  const rain = num(trends?.rain_change_pct);
  if (rain !== null) {
    const text = Math.abs(rain) < 2 ? `Since ${since} it rains about the same as in ${baseText}.`
      : rain < 0 ? `Since ${since} it rains about ${fmt(-rain, 0)}% less than in ${baseText}.`
        : `Since ${since} it rains about ${fmt(rain, 0)}% more than in ${baseText}.`;
    out.push({ icon: rain <= -2 ? "trend-down" : rain >= 2 ? "trend-up" : "trend-flat", text });
  }
  const heat = num(trends?.heat_days_change);
  if (heat !== null) {
    const text = Math.abs(heat) < 0.5 ? `About the same number of very hot days as in ${baseText}.`
      : heat > 0 ? `About ${fmt(heat, 0)} more very hot days a year than in ${baseText}.`
        : `About ${fmt(-heat, 0)} fewer very hot days a year than in ${baseText}.`;
    out.push({ icon: heat >= 0.5 ? "trend-up" : heat <= -0.5 ? "trend-down" : "trend-flat", text });
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

/** Readable crop name: from the API catalogue, else "durum_wheat" -> "Durum wheat". */
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
  // An example field is only worth suggesting when the farmer chose their own point on the map.
  const orExample = freePoint ? ", or pick an example field" : "";
  switch (kind) {
    case "offline":
      return {
        title: "You're offline",
        text: freePoint
          ? "A new map point needs internet to get NASA data. Connect and try again, or pick an example field."
          : "Only results you opened before on this phone work offline. Connect to the internet, or use your last answers.",
      };
    case "timeout":
      return {
        title: "NASA data is slow right now",
        text: `Try again in 1 minute${orExample}.`,
      };
    case "nasa":
      return {
        title: "We couldn't reach NASA data right now",
        text: `Try again in 1 minute${orExample}.`,
      };
    case "validation":
      return {
        title: "We couldn't use some answers",
        text: "Check the crop for each year.",
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
        text: `Try again in 1 minute${orExample}.`,
      };
  }
}

/** HTTP status -> error kind (see errorMessage). */
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

/** Lower case, no accents, single spaces: "  Maíz " -> "maiz". */
export function normalizeText(text) {
  return String(text ?? "").normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[_\s]+/g, " ").trim();
}

/**
 * Crop id for what the farmer typed in a crop text field, or null.
 * Exact name or id first (case and accents ignored); otherwise the only crop whose name starts with,
 * or else contains, the text ("sunfl" -> sunflower). Ambiguous or unknown text -> null.
 */
export function findCrop(text, crops) {
  const hits = matchCrops(text, crops);
  return hits.length === 1 ? hits[0].id : null;
}

/** Text of a crop suggestion: English name plus the Latin name, so either can be typed to find it. */
export function cropOption(crop) {
  return crop.scientific_name ? `${crop.name} · ${crop.scientific_name}` : crop.name;
}

/**
 * Crops that match what the farmer typed: by common (English) name, Latin (scientific) name, id or the full suggestion
 * text. Exact matches win; otherwise names that start with the text, then names that contain it.
 * Several hits = ambiguous (e.g. "Phaseolus vulgaris" is both green and dry bean).
 */
export function matchCrops(text, crops) {
  const q = normalizeText(text);
  if (!q) return [];
  const keys = (c) => [c.name, c.scientific_name, c.id, cropOption(c)].filter(Boolean).map(normalizeText);
  const exact = crops.filter((c) => keys(c).includes(q));
  if (exact.length) return exact;
  for (const test of [(k) => k.startsWith(q), (k) => k.includes(q)]) {
    const hits = crops.filter((c) => keys(c).some(test));
    if (hits.length) return hits;
  }
  return [];
}

// Limits per value (#44): the API sends one "what this can't tell" sentence per climate value (profile.field_limits),
// per score (score_limits) and per prediction (predictions.limits). Shown collapsed, next to the values they describe.
export const FIELD_LIMIT_ROWS = [
  ["rain_mm", "Rain"], ["et0_mm", "Water lost by a short grass field"], ["water_balance_mm", "Balance"],
  ["soil_wetness", "Soil moisture"], ["frost_days", "Frost days"], ["heat_days", "Hot days (over 35 °C)"],
  ["heavy_rain_days", "Very heavy rain days"], ["ndvi", "Plant cover"], ["likely_bare", "Bare months"],
];

/** "36.95° N, 4.55° W" (2 decimals, about 1 km); "—" when a value is missing. */
export function fmtCoords(lat, lon) {
  const a = num(lat), b = num(lon);
  if (a === null || b === null) return "—";
  return `${Math.abs(a).toFixed(2)}° ${a < 0 ? "S" : "N"}, ${Math.abs(b).toFixed(2)}° ${b < 0 ? "W" : "E"}`;
}

/**
 * Evidence sentence from the API in plain words: {text, confidence: "high"|"medium"|"low"|null, sources: ["R-01", …]}.
 * The "[R-01;R-02, confidence medium]" bracket becomes `sources` + `confidence`; indicator codes (I-01) and dataset
 * names are dropped from the text ("(NASA POWER 2005-2025, I-01)" -> "(NASA data 2005–2025)").
 */
export function plainEvidence(text) {
  let t = String(text ?? "");
  let confidence = null, sources = [];
  const bracket = /\s*\[([^\]]*)\]/.exec(t);
  if (bracket) {
    const conf = /confidence\s+(high|medium|low)\b/i.exec(bracket[1]);
    confidence = conf ? conf[1].toLowerCase() : null;
    sources = bracket[1].replace(/,?\s*confidence\s+\S+/i, "").split(/[;,]/).map((s) => s.trim())
      .filter((s) => /^[A-Z]+-[A-Z0-9]+$/.test(s));
    t = t.replace(bracket[0], "");
  }
  t = t
    .replace(/\(NASA POWER (\d{4})-(\d{4})(?:,\s*I-\d+)*\)/g, "(NASA data $1–$2)")
    .replace(/\(MODIS NDVI (\d{4})-(\d{4})(?:,\s*I-\d+)*\)/g, "(satellite photos $1–$2)")
    .replace(/,\s*I-\d+/g, "")
    .replace(/\s*\(I-\d+(?:,\s*I-\d+)*\)/g, "")
    .replace(/Satellite greenness suggests/g, "Satellite photos suggest")
    .replace(/(^|[^-\w])water need/g, (m, p) => `${p}crop water need`)
    .replace(/crop crop water need/g, "crop water need")
    .replace(/\b(\d{4})-(\d{4})\b/g, "$1–$2")
    .replace(/\s{2,}/g, " ")
    .trim();
  return { text: t, confidence, sources };
}

/** Collapsed list of [label, sentence] rows; rows without a sentence are skipped; "" when none is left
 * (e.g. an analysis saved offline before the API sent limits). */
export function limitsDetails(summary, rows) {
  const items = rows.filter(([, text]) => typeof text === "string" && text.trim());
  if (!items.length) return "";
  return `<details class="limits-box"><summary>${esc(summary)}</summary><ul class="limits">${
    items.map(([label, text]) => `<li><strong>${esc(label)}:</strong> ${esc(text)}</li>`).join("")}</ul></details>`;
}
