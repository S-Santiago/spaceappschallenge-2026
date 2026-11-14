// Tests for the "What to expect" tab (#40). Run: node --test "tests/web/*.test.mjs"
// Fixture: real GET /api/predictions output for Vega de Antequera with its demo rotation
// (durum wheat, durum wheat, sunflower), saved in tests/fixtures/predictions_antequera.json.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { predictionsQuery } from "../../web/js/api.js";
import { renderExpect, alertsSection, rainStrip } from "../../web/js/expect.js";
import {
  BASIS, FROST_CAVEAT, alertCards, basisFor, count, frostSentences, heatFacts, heavySentence, mmdd, nextWeeks, rainSentence,
  rainYearSummary, returnSentence, weekOfYear,
} from "../../web/js/expect-format.js";

const PRED = JSON.parse(readFileSync(new URL("../fixtures/predictions_antequera.json", import.meta.url), "utf8"));
const TODAY = new Date(2026, 10, 14); // 14 Nov 2026 → week 46 (12–18 Nov)
const RED_ALERT = /undefined|NaN|null|None|\[object/;
const heatProfile = (days, trends = { heat_days_change: 13.2, baseline: "2005-2014" }) => ({
  months: days.map((d, i) => ({ month: i + 1, heat_days: d })), trends,
});
const ANTEQUERA_HEAT = [0, 0, 0, 0, 0, 1.9, 10.2, 9.4, 0.4, 0, 0, 0];

test("weekOfYear matches predictions.week_of_year (week 52 takes the last days, leap day = 28 Feb)", () => {
  assert.equal(weekOfYear(new Date(2026, 0, 1)), 1);
  assert.equal(weekOfYear(new Date(2026, 0, 8)), 2);
  assert.equal(weekOfYear(TODAY), 46);
  assert.equal(weekOfYear(new Date(2026, 11, 31)), 52);
  assert.equal(weekOfYear(new Date(2028, 1, 29)), weekOfYear(new Date(2028, 1, 28)));
});

test("next 4 weeks start with the week of today and wrap over New Year", () => {
  assert.deepEqual(nextWeeks(PRED.rain_weeks, TODAY).map((w) => w.start), ["11-12", "11-19", "11-26", "12-03"]);
  assert.deepEqual(nextWeeks(PRED.rain_weeks, new Date(2026, 11, 28)).map((w) => w.week), [52, 1, 2, 3]);
  assert.deepEqual(nextWeeks(null, TODAY), []);
});

test("rain sentence follows docs/indicators.md with year counts", () => {
  const w48 = PRED.rain_weeks.find((w) => w.week === 48);
  assert.equal(rainSentence(w48), "In the week of 26 Nov it rained in 16 of the last 21 years (in 9 of them more than 10 mm).");
  assert.equal(rainSentence({ start: "07-16", prob_rain: 0, prob_useful_rain: 0, years: 21 }),
    "In the week of 16 Jul it did not rain in any of the last 21 years.");
  assert.equal(rainSentence({ start: "07-23", prob_rain: 0.05, prob_useful_rain: 0, years: 21 }),
    "In the week of 23 Jul it rained in 1 of the last 21 years (never more than 10 mm).");
  assert.equal(rainSentence({ start: "x", prob_rain: 0.5, years: 21 }), null);
  assert.equal(count(0.76, 21), 16);
});

test("year summary names wet and dry months", () => {
  const s = rainYearSummary(PRED.rain_weeks);
  assert.match(s, /^Rain came in at least half of the years in most weeks of .+, and in fewer than 1 year in 5 in .*July/);
  assert.equal(rainYearSummary(PRED.rain_weeks.slice(0, 10)), null);
});

test("frost sentences: Antequera, frost-free valley and missing data", () => {
  const f = frostSentences(PRED.frost);
  assert.equal(f.spring, "In 19 of the last 21 years the last frost came on or before 14 March.");
  assert.equal(f.autumn, "In 19 of the last 21 years the first frost came on or after 3 December (or not at all before the new year).");
  assert.equal(f.safe, "That leaves about 264 days without frost in most years, between 14 March and 3 December.");

  const none = frostSentences({
    spring: { years: 21, years_with_frost: 0, last_frost_p90: null, years_by_p90: 21 },
    autumn: { years: 21, years_with_frost: 0, first_frost_p10: null, years_from_p10: 21 }, safe_days: 365,
  });
  assert.equal(none.spring, "No frost in the last 21 years in this area.");
  assert.equal(none.autumn, null);
  assert.equal(none.safe, null);

  const rare = frostSentences({
    spring: { years: 21, years_with_frost: 1, last_frost_p90: null, years_by_p90: 20 },
    autumn: { years: 21, years_with_frost: 0, first_frost_p10: null, years_from_p10: 21 }, safe_days: 365,
  });
  assert.equal(rare.spring, "In 20 of the last 21 years there was no frost in spring.");
  assert.equal(rare.autumn, "No frost in the last 21 years in this area.");
  assert.equal(rare.safe, "In most years there is no frost at all.");
  assert.deepEqual(frostSentences(null), { spring: null, autumn: null, safe: null, none: false });
});

test("heat comes from the profile months (I-06), nothing new", () => {
  const h = heatFacts(heatProfile(ANTEQUERA_HEAT));
  assert.equal(h.summary, "About 22 very hot days (over 35 °C) a year, mostly in June–August.");
  assert.deepEqual(h.perMonth, ["June: about 2 days", "July: about 10 days", "August: about 9 days"]);
  assert.equal(heatFacts(heatProfile(Array(12).fill(0))).summary, "Very hot days (over 35 °C) are rare here.");
  assert.equal(heatFacts(heatProfile([null, ...Array(11).fill(0)])), null);
  assert.equal(heatFacts({}), null);
});

test("heavy rain sentences (P-02) match docs/indicators.md", () => {
  const nov = PRED.heavy_rain.months.find((m) => m.month === 11);
  assert.equal(heavySentence(nov), "In November, a day with more than 20 mm of rain happened in 11 of the last 21 years.");
  assert.equal(heavySentence({ month: 7, prob: 0, years: 21 }), "In July, no day with more than 20 mm of rain in the last 21 years.");
  assert.equal(returnSentence(PRED.heavy_rain), "About once every 5 years a single day brings 42 mm or more.");
  assert.equal(returnSentence({}), null);
});

test("alert cards (P-07): upcoming first, icon + word, source, no 'erosion measured'", () => {
  const cards = alertCards(PRED.alerts, 20, TODAY);
  assert.deepEqual(cards.map((c) => [c.month, c.level]), [[11, "high"], [12, "medium"], [2, "medium"], [10, "medium"]]);
  assert.equal(cards[0].text, "Your field is usually bare and heavy rain is common (11 of 21 years). Bare soil can wash away — a cover crop or leaving stubble helps.");
  assert.equal(cards[0].levelWord, "High");
  assert.equal(cards[0].icon, "⚠️");
  assert.equal(cards[0].source, "crop calendar");
  assert.equal(alertCards([{ month: 3, prob: 0.3, years: 21, sources: ["satellite", "crop_calendar"], level: "medium" }], 20, TODAY)[0].source,
    "satellite and crop calendar");
  for (const c of cards) assert.doesNotMatch(c.text, /erosion/i);
});

test("the alert section is absent unless the payload has alerts", () => {
  assert.equal(alertsSection({ ...PRED, alerts: null }, TODAY), "");
  assert.equal(alertsSection({ ...PRED, alerts: [] }, TODAY), "");
  const { alerts, ...withoutKey } = PRED;
  assert.equal(alertsSection(withoutKey, TODAY), "");
  assert.equal(alertsSection({ alerts: [{ month: 11, level: "unknown" }] }, TODAY), "");
  const html = alertsSection(PRED, TODAY);
  assert.match(html, /Heavy rain on bare soil/);
  assert.match(html, /heavy-rain days often fall when the field is bare/i);
  assert.match(html, /<span class="level">High<\/span>/);
  assert.equal((html.match(/class="card exp-card alert/g) || []).length, 1); // one card, one row per month
  assert.equal((html.match(/<li>/g) || []).length, 4);
});

test("the full tab: basis once at the top (not in every card), frost caveat always, no red-alert text", () => {
  const html = renderExpect(PRED, heatProfile(ANTEQUERA_HEAT), TODAY);
  const cards = html.match(/<article class="card exp-card[^]*?<\/article>/g);
  assert.equal(cards.length, 5, `cards: ${cards.length}`); // alerts, rain weeks, frost, heat, heavy
  for (const c of cards) assert.ok(!c.includes("not a weather forecast"), c.slice(0, 80));
  assert.ok(html.startsWith(`<p class="basis basis--lead">ℹ️ ${BASIS}`));
  assert.equal(BASIS, "Based on 21 years of NASA data (2005–2025) — not a weather forecast.");
  assert.ok(html.includes(FROST_CAVEAT));
  assert.ok(html.includes("<strong>This week (from 12 Nov)</strong>"));
  assert.ok(html.includes("<strong>Week of 26 Nov</strong>: rain in 16 of 21 years, 9 with more than 10 mm"));
  assert.ok(html.includes("About 13 more very hot days a year than in 2005–2014."));
  assert.doesNotMatch(html.replace(/aria-[a-z]+="[^"]*"/g, ""), RED_ALERT);
  assert.doesNotMatch(html, /forecast says|will rain|erosion measured/i);
});

test("frost caveat is shown even in a frost-free valley", () => {
  const html = renderExpect({ ...PRED, frost: {
    spring: { years: 21, years_with_frost: 0, years_by_p90: 21 }, autumn: { years: 21, years_with_frost: 0, years_from_p10: 21 }, safe_days: 365,
  } }, heatProfile(ANTEQUERA_HEAT), TODAY);
  assert.ok(html.includes("No frost in the last 21 years in this area."));
  assert.ok(html.includes(FROST_CAVEAT));
});

test("empty payload gives a helpful empty state, never placeholders", () => {
  const html = renderExpect({}, {}, TODAY);
  assert.match(html, /not available for this field/);
  assert.doesNotMatch(html.replace(/aria-[a-z]+="[^"]*"/g, ""), RED_ALERT);
});

test("52-week strip: one bar per week, today marked, accessible summary", () => {
  const svg = rainStrip(PRED.rain_weeks, TODAY);
  assert.equal((svg.match(/<rect /g) || []).length, 52);
  assert.match(svg, /▼ Today/);
  assert.match(svg, /role="img" aria-label="Chance of rain in each week of the year[^"]*week of 12 November/);
  assert.equal(rainStrip(PRED.rain_weeks.slice(1), TODAY), "");
  assert.equal(mmdd("11-26", true), "26 November");
});

test("predictions query: demo field or point, current rotation repeated, slope", () => {
  assert.equal(predictionsQuery({ field: "antequera", rotation: ["durum_wheat", "sunflower"], slope: "flat" }),
    "field=antequera&rotation=durum_wheat&rotation=sunflower&slope=flat");
  assert.equal(predictionsQuery({ lat: 37.1, lon: -4.6, rotation: [], slope: "steep" }), "lat=37.1&lon=-4.6&slope=steep");
});

test("basis line follows the API period", () => {
  assert.equal(basisFor("2005-2025"), "Based on 21 years of NASA data (2005–2025) — not a weather forecast.");
  assert.equal(basisFor("2006-2025"), "Based on 20 years of NASA data (2006–2025) — not a weather forecast.");
  assert.equal(basisFor(null), BASIS);
});
