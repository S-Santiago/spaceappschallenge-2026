// Pure helpers for the "What to expect" screen (P-01, P-02, P-03, P-07 from GET /api/predictions, and heat from
// the Shape 1 profile). No DOM here, so `node --test tests/web` can check them. Sentences follow
// docs/indicators.md → "Farmer sentences": counts of years, never percentages; nothing is invented, and a
// missing value means the sentence is skipped.

import { MONTHS, MONTH_ABBR, fmt, formatRuns, monthRuns, num } from "./format.js";

export const BASIS = "Based on the last 20 years of NASA data — not a weather forecast.";
export const FROST_CAVEAT = "Frost near the ground and in valley bottoms can come later and be harder than shown. Check with local experience.";
export const WEEKS = 52;

/** Years out of `years` for a 0–1 share, as a whole count (21 × 0.76 → 16). */
export function count(prob, years) {
  const p = num(prob), y = num(years);
  return p === null || y === null ? null : Math.round(p * y);
}

/** "11-26" → "26 Nov"; "26 November" with `long`. */
export function mmdd(text, long = false) {
  const m = /^(\d{2})-(\d{2})$/.exec(String(text ?? ""));
  if (!m) return null;
  const month = Number(m[1]), day = Number(m[2]);
  if (month < 1 || month > 12) return null;
  return `${day} ${(long ? MONTHS : MONTH_ABBR)[month - 1]}`;
}

/** Week of the year as in predictions.week_of_year: week 1 = 1–7 Jan, week 52 takes the last 1–2 days. */
export function weekOfYear(date) {
  const month = date.getMonth(), day = month === 1 ? Math.min(date.getDate(), 28) : date.getDate();
  const doy = Math.round((Date.UTC(2001, month, day) - Date.UTC(2001, 0, 1)) / 86400000) + 1; // non-leap year
  return Math.min(Math.floor((doy - 1) / 7) + 1, WEEKS);
}

/** The week that contains `today` and the next n − 1 (wrapping over New Year). */
export function nextWeeks(rainWeeks, today = new Date(), n = 4) {
  const byWeek = new Map((rainWeeks || []).filter((w) => w && num(w.week) !== null).map((w) => [w.week, w]));
  const first = weekOfYear(today);
  const out = [];
  for (let i = 0; i < n; i++) {
    const w = byWeek.get(((first - 1 + i) % WEEKS) + 1);
    if (w) out.push(w);
  }
  return out;
}

/** P-01 sentence: "In the week of 26 Nov it rained in 16 of the last 21 years (in 9 of them more than 10 mm)." */
export function rainSentence(w) {
  const start = mmdd(w?.start), years = num(w?.years);
  const rainy = count(w?.prob_rain, years), useful = count(w?.prob_useful_rain, years);
  if (!start || !years || rainy === null) return null;
  if (rainy === 0) return `In the week of ${start} it did not rain in any of the last ${years} years.`;
  const detail = useful === null ? "" : useful === 0 ? " (never more than 10 mm)" : ` (in ${useful} of them more than 10 mm)`;
  return `In the week of ${start} it rained in ${rainy} of the last ${years} years${detail}.`;
}

/** Plain summary of the 52-week strip, for screen readers and as a caption. */
export function rainYearSummary(rainWeeks) {
  const weeks = (rainWeeks || []).filter((w) => num(w?.prob_rain) !== null && mmdd(w.start));
  if (weeks.length < WEEKS) return null;
  const byMonth = new Map();
  for (const w of weeks) {
    const m = Number(w.start.slice(0, 2));
    byMonth.set(m, [...(byMonth.get(m) || []), w.prob_rain]);
  }
  const mean = (m) => byMonth.get(m).reduce((a, b) => a + b, 0) / byMonth.get(m).length;
  const months = [...byMonth.keys()];
  const wet = months.filter((m) => mean(m) >= 0.5), dry = months.filter((m) => mean(m) < 0.2);
  const parts = [];
  if (wet.length) parts.push(`rain came in at least half of the years in most weeks of ${formatRuns(monthRuns(wet))}`);
  if (dry.length) parts.push(`in fewer than 1 year in 5 in ${formatRuns(monthRuns(dry))}`);
  if (!parts.length) return "Rain chances are similar all year.";
  const text = parts.join(", and ");
  return `${text[0].toUpperCase()}${text.slice(1)}.`;
}

/** P-03 sentences: {spring, autumn, safe}; any of them null when the data is missing. */
export function frostSentences(frost) {
  const out = { spring: null, autumn: null, safe: null, none: false };
  const s = frost?.spring, a = frost?.autumn;
  if (s && num(s.years)) {
    const last = mmdd(s.last_frost_p90, true);
    if (s.years_with_frost === 0) out.spring = `No frost in the last ${s.years} years in this area.`;
    else if (last && num(s.years_by_p90) !== null) out.spring = `In ${s.years_by_p90} of the last ${s.years} years the last frost came on or before ${last}.`;
    else if (num(s.years_by_p90) !== null) out.spring = `In ${s.years_by_p90} of the last ${s.years} years there was no frost in spring.`;
  }
  if (a && num(a.years)) {
    const first = mmdd(a.first_frost_p10, true);
    if (a.years_with_frost === 0) out.autumn = `No frost in the last ${a.years} years in this area.`;
    else if (first && num(a.years_from_p10) !== null) out.autumn = `In ${a.years_from_p10} of the last ${a.years} years the first frost came on or after ${first} (or not at all before the new year).`;
    else if (num(a.years_from_p10) !== null) out.autumn = `In ${a.years_from_p10} of the last ${a.years} years there was no frost before the new year.`;
  }
  out.none = s?.years_with_frost === 0 && a?.years_with_frost === 0;
  const days = num(frost?.safe_days);
  if (days !== null) {
    if (out.none) out.safe = null; // "No frost in the last N years" already says it
    else if (days >= 365) out.safe = "In most years there is no frost at all.";
    else {
      const from = mmdd(s?.last_frost_p90, true) || "1 January", to = mmdd(a?.first_frost_p10, true) || "31 December";
      out.safe = `That leaves about ${fmt(days, 0)} days without frost in most years, between ${from} and ${to}.`;
    }
  }
  if (out.none) out.autumn = null; // one "no frost" sentence is enough
  return out;
}

/** Heat from Shape 1 (I-06 monthly heat_days) and its 10-year change (I-11). No new statistics. */
export function heatFacts(profile) {
  const months = (profile?.months || []).filter((m) => m && m.month >= 1 && m.month <= 12);
  if (months.length !== 12 || months.some((m) => num(m.heat_days) === null)) return null;
  const total = months.reduce((acc, m) => acc + m.heat_days, 0);
  const hot = months.filter((m) => m.heat_days >= 0.5).sort((a, b) => a.month - b.month);
  const peak = hot.filter((m) => m.heat_days >= 1).map((m) => m.month);
  const summary = total < 0.5 ? "Very hot days (over 35 °C) are rare here."
    : `About ${fmt(total, 0)} very hot days (over 35 °C) a year${peak.length ? `, mostly in ${formatRuns(monthRuns(peak))}` : ""}.`;
  const perMonth = hot.map((m) => `${MONTHS[m.month - 1]}: about ${fmt(m.heat_days, 0)} ${Math.round(m.heat_days) === 1 ? "day" : "days"}`);
  return { summary, perMonth };
}

/** P-02 sentence for one month: "In November, a day with more than 20 mm of rain happened in 11 of the last 21 years." */
export function heavySentence(row, thresholdMm = 20) {
  const years = num(row?.years), n = count(row?.prob, years);
  if (!row || row.month < 1 || row.month > 12 || !years || n === null) return null;
  const month = MONTHS[row.month - 1];
  return n === 0 ? `In ${month}, no day with more than ${fmt(thresholdMm, 0)} mm of rain in the last ${years} years.`
    : `In ${month}, a day with more than ${fmt(thresholdMm, 0)} mm of rain happened in ${n} of the last ${years} years.`;
}

/** P-02 return level: "About once every 5 years a single day brings 42 mm or more." */
export function returnSentence(heavy, period = 5) {
  const level = (heavy?.return_levels || []).find((r) => r.years === period);
  return level && num(level.mm) !== null ? `About once every ${period} years a single day brings ${fmt(level.mm, 0)} mm or more.` : null;
}

/** Months from `from` (1–12) onwards, wrapping: upcoming first. */
export function fromMonth(items, from, key = "month") {
  return [...(items || [])].sort((a, b) => ((a[key] - from + 12) % 12) - ((b[key] - from + 12) % 12));
}

const LEVELS = { high: { icon: "⚠️", word: "High" }, medium: { icon: "🔶", word: "Medium" } };
const SOURCES = { crop_calendar: "crop calendar", satellite: "satellite" };

/**
 * P-07 alert cards, upcoming months first. Empty when the payload has no alerts (null = bare months
 * unknown, [] = none): the section is then not shown at all. Wording: heavy-rain days often fall when the
 * field is bare — a proxy, never "erosion measured".
 */
export function alertCards(alerts, thresholdMm = 20, today = new Date()) {
  if (!Array.isArray(alerts)) return [];
  return fromMonth(alerts.filter((a) => a && LEVELS[a.level] && a.month >= 1 && a.month <= 12), today.getMonth() + 1)
    .map((a) => {
      const n = count(a.prob, a.years);
      const freq = n === null ? "" : ` (${n} of ${a.years} years)`;
      const rain = a.level === "high" ? `heavy rain is common${freq}` : `heavy rain comes in some years${freq}`;
      return {
        month: a.month,
        level: a.level,
        icon: LEVELS[a.level].icon,
        title: `${MONTHS[a.month - 1]} · ${LEVELS[a.level].word.toLowerCase()}`,
        levelWord: LEVELS[a.level].word,
        text: `Your field is usually bare and ${rain}. Bare soil can wash away — a cover crop or leaving stubble helps.`,
        source: (a.sources || []).map((s) => SOURCES[s]).filter(Boolean).join(" and "),
        threshold: `A heavy-rain day here means more than ${fmt(thresholdMm, 0)} mm in one day.`,
      };
    });
}
