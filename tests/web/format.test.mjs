// Unit tests for the PWA helpers. Run: node --test tests/web
import assert from "node:assert/strict";
import { test } from "node:test";

import {
  cropName, errorKind, errorMessage, esc, fmt, formatRuns, keyFacts, levelText, monthRuns, ndviMissing, trendFacts,
} from "../../web/js/format.js";

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
  assert.equal(t[0].text, "It rains about 15% less than in 2005–2014.");
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
