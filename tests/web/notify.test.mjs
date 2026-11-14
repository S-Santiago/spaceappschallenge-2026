// Tests for heavy-rain warnings on this phone (#42). Run: node --test "tests/web/*.test.mjs"
// Fixture: real GET /api/predictions for Vega de Antequera (alerts: Feb medium, Oct medium, Nov high, Dec medium).
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { alertsSection } from "../../web/js/expect.js";
import {
  dedupeKey, dueAlerts, emptyStore, fieldKey, keepAlerts, markSent, monthKey, pendingWarnings, warnState, warningHash,
  warningText,
} from "../../web/js/notify-format.js";

const PRED = JSON.parse(readFileSync(new URL("../fixtures/predictions_antequera.json", import.meta.url), "utf8"));
const NOV = new Date(2026, 10, 14);
const RED_ALERT = /undefined|NaN|null|None|\[object/;
const store = (alerts = PRED.alerts, sent = []) => ({ fields: { "field:antequera": { name: "Vega de Antequera", alerts: keepAlerts(alerts) } }, sent });

test("field key is the demo slug or the point rounded to ~1 km, never the farmer's answers", () => {
  assert.equal(fieldKey({ field: "antequera", rotation: ["durum_wheat"], priorities: { water: 3 } }), "field:antequera");
  assert.equal(fieldKey({ lat: 36.71834, lon: -4.4214 }), "point:36.72,-4.42");
  assert.equal(fieldKey({}), null);
  assert.equal(monthKey(2027, 1), "2027-01");
  assert.equal(dedupeKey("field:antequera", "2026-11"), "field:antequera|2026-11");
});

test("only this month and next month trigger, with the YYYY-MM of the alerted month", () => {
  assert.deepEqual(dueAlerts(PRED.alerts, NOV).map((a) => [a.month, a.ym]), [[11, "2026-11"], [12, "2026-12"]]);
  assert.deepEqual(dueAlerts(PRED.alerts, new Date(2026, 8, 20)).map((a) => a.ym), ["2026-10"]); // Sep: next is Oct
  assert.deepEqual(dueAlerts(PRED.alerts, new Date(2026, 11, 31)).map((a) => a.ym), ["2026-12"]); // Jan not alerted
  assert.deepEqual(dueAlerts(PRED.alerts, new Date(2027, 0, 10)).map((a) => a.ym), ["2027-02"]); // wraps the year
  assert.deepEqual(dueAlerts(PRED.alerts, new Date(2026, 6, 1)), []); // July: nothing near
  assert.deepEqual(dueAlerts(null, NOV), []);
  assert.deepEqual(dueAlerts([{ month: 11, level: "unknown" }, { month: 13, level: "high" }], NOV), []);
});

test("one notification per field per month: dedupe keys stop repeats, old keys are dropped", () => {
  const first = pendingWarnings(store(), NOV);
  assert.deepEqual(first.map((w) => w.dedupe), ["field:antequera|2026-11", "field:antequera|2026-12"]);
  const after = markSent(store(), first.map((w) => w.dedupe), NOV);
  assert.deepEqual(pendingWarnings(after, NOV), []);
  // In December, November's key no longer matters and December's was already shown.
  assert.deepEqual(pendingWarnings(after, new Date(2026, 11, 2)), []);
  // A year later the same months warn again.
  assert.equal(pendingWarnings(after, new Date(2027, 10, 3)).length, 2);
  const pruned = markSent(after, ["field:antequera|2028-02"], new Date(2028, 1, 1));
  assert.deepEqual(pruned.sent, ["field:antequera|2028-02"]);
  assert.deepEqual(pendingWarnings(emptyStore(), NOV), []);
});

test("message text: P-07 wording, level as a word, year counts, not a forecast", () => {
  const nov = keepAlerts(PRED.alerts).find((a) => a.month === 11);
  const t = warningText("Vega de Antequera", nov);
  assert.equal(t.title, "Heavy-rain risk on bare soil — Vega de Antequera");
  assert.equal(t.body, "High risk in November: heavy rain often falls on bare soil (11 of 21 years). " +
    "Keep stubble or a cover crop. Past NASA data, not a forecast.");
  const dec = warningText("Vega de Antequera", keepAlerts(PRED.alerts).find((a) => a.month === 12), { example: true });
  assert.equal(dec.title, "Example: Heavy-rain risk on bare soil — Vega de Antequera");
  assert.match(dec.body, /^Medium risk in December: .*\(5 of 21 years\)/);
  assert.equal(warningText("", { month: 2, level: "medium" }).body,
    "Medium risk in February: heavy rain often falls on bare soil. Keep stubble or a cover crop. Past NASA data, not a forecast.");
  assert.match(warningText(null, nov).title, /— your field$/);
  assert.equal(warningText("x", { month: 2, level: "low" }), null);
  for (const a of keepAlerts(PRED.alerts)) {
    const { title, body } = warningText("Vega de Antequera", a);
    assert.ok(!RED_ALERT.test(title + body), body);
    assert.ok(!/erosion|will rain|forecast:/i.test(body), body);
  }
});

test("control state: unsupported and blocked are explained, on needs permission and this field", () => {
  assert.equal(warnState({ supported: false, permission: "granted", watched: true }), "unsupported");
  assert.equal(warnState({ supported: true, permission: "denied", watched: true }), "denied");
  assert.equal(warnState({ supported: true, permission: "granted", watched: true }), "on");
  assert.equal(warnState({ supported: true, permission: "granted", watched: false }), "off");
  assert.equal(warnState({ supported: true, permission: "default", watched: true }), "off");
});

test("the link opens the field's What to expect; the alert card carries a hidden slot (no dead button)", () => {
  assert.equal(warningHash("point:36.72,-4.42"), "#/warning/point%3A36.72%2C-4.42");
  const html = alertsSection(PRED, NOV);
  assert.match(html, /<div class="warn" id="warn-slot" hidden><\/div>/);
  assert.ok(!/<button/.test(html));
});
