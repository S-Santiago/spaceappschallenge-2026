// Unit tests for the PWA helpers. Run: node --test tests/web
import assert from "node:assert/strict";
import { test } from "node:test";

import {
  FIELD_LIMIT_ROWS, cropName, errorKind, errorMessage, esc, fmt, formatRuns, keyFacts, levelText, limitsDetails, monthRuns,
  fmtCoords, ndviMissing, plainEvidence, trendFacts,
} from "../../web/js/format.js";
import { ICON_NAMES, icon, withIcon } from "../../web/js/icons.js";

const month = (m, extra = {}) => ({
  month: m, rain_mm: 40, et0_mm: 60, water_balance_mm: -20, soil_wetness: 0.4,
  frost_days: 0, heat_days: 0, heavy_rain_days: 0, ndvi: 0.4, likely_bare: false, ...extra,
});
const profile = (fn = () => ({})) => ({ months: Array.from({ length: 12 }, (_, i) => month(i + 1, fn(i + 1))) });
const RED_ALERT = /undefined|NaN|null|None|\[object/;

test("fmt never prints undefined, NaN or null", () => {
  for (const v of [undefined, null, NaN, Infinity, "12", {}]) assert.equal(fmt(v, 0, "mm"), "—");
  assert.equal(fmt(12.345, 1, "mm"), "12.3 mm");
  assert.equal(fmt(-4.6, 0), "−5");
});

test("esc escapes markup from data", () => {
  assert.equal(esc('<img src=x onerror="a">'), "&lt;img src=x onerror=&quot;a&quot;&gt;");
  assert.equal(esc(undefined), "");
});

test("monthRuns wraps over New Year", () => {
  assert.deepEqual(monthRuns([11, 12, 1, 5]), [[5, 5], [11, 1]]);
  assert.deepEqual(monthRuns([]), []);
  assert.deepEqual(monthRuns([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]), [[1, 12]]);
  assert.equal(formatRuns([[10, 3], [6, 6]]), "October–March and June");
});

test("keyFacts derives sentences from the profile and skips missing data", () => {
  const facts = keyFacts(profile((m) => (m >= 6 && m <= 8 ? { heat_days: 5, likely_bare: true, ndvi: 0.2 } : {})));
  const text = facts.map((f) => f.text).join(" ");
  assert.match(text, /480 mm of rain a year/);
  assert.match(text, /probably bare in June–August/);
  assert.match(text, /About 15 very hot days/);
  assert.doesNotMatch(text, RED_ALERT);
  for (const f of facts) assert.ok(ICON_NAMES.includes(f.icon), `icon name: ${f.icon}`); // a name, not a pictogram
  assert.deepEqual(keyFacts({ months: [] }), []);
  assert.deepEqual(keyFacts(undefined), []);
});

test("without MODIS greenness there is no bare-field sentence", () => {
  const p = profile(() => ({ ndvi: null, likely_bare: null }));
  assert.equal(ndviMissing(p), true);
  assert.ok(keyFacts(p).every((f) => !/bare|covered/.test(f.text)));
});

test("a month with a missing value drops only that fact", () => {
  const facts = keyFacts(profile((m) => (m === 3 ? { rain_mm: null } : {})));
  assert.ok(facts.length > 0);
  assert.ok(facts.every((f) => !/of rain a year/.test(f.text)));
  assert.doesNotMatch(facts.map((f) => f.text).join(" "), RED_ALERT);
});

test("trendFacts", () => {
  const t = trendFacts({ rain_change_pct: -14.6, heat_days_change: 13.2, baseline: "2005-2014" });
  assert.equal(t[0].text, "Since 2016 it rains about 15% less than in 2005–2014.");
  assert.equal(t[0].icon, "trend-down");
  assert.equal(t[1].icon, "trend-up");
  assert.equal(t[1].text, "About 13 more very hot days a year than in 2005–2014.");
  assert.deepEqual(trendFacts({ rain_change_pct: null }), []);
});

test("levels and crop names", () => {
  assert.equal(levelText("good", 80), "Good");
  assert.equal(levelText(undefined, 50), "Fair");
  assert.equal(levelText(undefined, undefined), "Not available");
  assert.equal(cropName("durum_wheat", {}), "Durum wheat");
  assert.equal(cropName("maize", { maize: "Maize (grain)" }), "Maize (grain)");
});

test("every HTTP error maps to a plain-English message", () => {
  assert.equal(errorKind(422), "validation");
  assert.equal(errorKind(404), "not_found");
  assert.equal(errorKind(503), "nasa");
  assert.equal(errorKind(500), "server");
  for (const kind of ["offline", "timeout", "nasa", "validation", "not_found", "network", "server", "???"]) {
    const m = errorMessage(kind, { freePoint: true });
    assert.ok(m.title && m.text);
    assert.doesNotMatch(m.title + m.text, /error|exception|traceback|\d{3}|undefined/i);
  }
});

test("limitsDetails lists only rows with a sentence, escaped, and is empty without any (#44)", () => {
  const html = limitsDetails("What the scores can not tell", [["Water", "Rain <vs> need"], ["Soil", undefined], ["Income", ""]]);
  assert.ok(html.startsWith("<details"));
  assert.ok(html.includes("<strong>Water:</strong> Rain &lt;vs&gt; need"));
  assert.ok(!html.includes("Soil") && !html.includes("Income"));
  assert.equal(limitsDetails("x", [["Water", undefined]]), "");
  assert.doesNotMatch(html, RED_ALERT);
});

test("FIELD_LIMIT_ROWS covers every monthly value of the profile (#44)", () => {
  const keys = Object.keys(month(1)).filter((k) => k !== "month").sort();
  assert.deepEqual(FIELD_LIMIT_ROWS.map(([k]) => k).sort(), keys);
});

test("fmtCoords prints hemispheres and two decimals", () => {
  assert.equal(fmtCoords(36.9512, -4.5489), "36.95° N, 4.55° W");
  assert.equal(fmtCoords(-12.3, 45), "12.30° S, 45.00° E");
  assert.equal(fmtCoords(null, 4), "—");
});

test("plainEvidence moves sources and confidence out of the sentence and drops indicator codes", () => {
  const e = plainEvidence("Durum wheat: rain Nov-Jun averages 420 mm (NASA POWER 2005-2025, I-01), plus about 60 mm stored " +
    "in the soil from earlier rain, vs a water need of 450-650 mm [R-01;R-02;R-03;R-IND, confidence medium]");
  assert.equal(e.confidence, "medium");
  assert.deepEqual(e.sources, ["R-01", "R-02", "R-03", "R-IND"]);
  assert.ok(e.text.includes("(NASA data 2005–2025)"), e.text);
  assert.ok(e.text.endsWith("vs a crop water need of 450-650 mm"), e.text);
  assert.ok(!/I-0|NASA POWER|confidence/.test(e.text) && !e.text.includes("["), e.text);
  assert.equal(plainEvidence("Satellite greenness suggests a bare field in July (MODIS NDVI 2024-2025, I-09)").text,
    "Satellite photos suggest a bare field in July (satellite photos 2024–2025)");
  assert.equal(plainEvidence("Cover crop period: 300 mm (NASA POWER 2005-2025, I-01, I-07)").text,
    "Cover crop period: 300 mm (NASA data 2005–2025)");
  assert.deepEqual(plainEvidence("x [no source, confidence unknown]"), { text: "x", confidence: null, sources: [] });
  assert.deepEqual(plainEvidence(undefined), { text: "", confidence: null, sources: [] });
});

test("icons are decorative inline SVG drawn with currentColor", () => {
  for (const name of ICON_NAMES) {
    const svg = icon(name);
    assert.ok(svg.startsWith('<svg class="icon"'), name);
    assert.ok(svg.includes('aria-hidden="true"') && svg.includes('focusable="false"'), name);
    assert.ok(svg.includes('viewBox="0 0 24 24"') && svg.includes('stroke="currentColor"'), name);
    assert.ok(svg.endsWith("</svg>"), name);
  }
  for (const name of ["drop", "sprout", "coins", "shield", "pin", "check", "back", "next", "warning", "info", "rain", "storm",
    "frost", "sun", "heat", "leaf", "bare", "stubble", "unknown", "trend-up", "trend-down", "trend-flat", "bell", "bell-off",
    "today", "legend-bar", "legend-line", "more", "chevron-right"]) assert.ok(ICON_NAMES.includes(name), name);
  assert.equal(icon("nope"), "");
  assert.equal(withIcon("drop", "Water"), `<span class="with-icon">${icon("drop")}<span>Water</span></span>`);
});
