// Live progress steps (web/js/progress-steps.js). Run: node --test tests/web
import assert from "node:assert/strict";
import { test } from "node:test";

import { analysisSteps, announcement, formatElapsed, modisLine, shouldPollProgress } from "../../web/js/progress-steps.js";

const modis = (extra) => ({ state: "running", elapsed_s: 20, batches_done: 0, batches_total: 5, attempt: 1, attempts_max: 4, ...extra });
const states = (steps) => steps.map((s) => s.state);

test("before any progress: asking NASA, satellite asked, compare waits", () => {
  const steps = analysisSteps(null);
  assert.deepEqual(states(steps), ["active", "active", "waiting"]);
  assert.equal(steps[0].label, "NASA weather data (POWER)");
  assert.equal(steps[1].label, "Satellite photos (MODIS)");
  assert.equal(steps[2].label, "Comparing rotations");
});

test("steps follow the server counters", () => {
  const steps = analysisSteps({ power: { state: "done" }, modis: modis({ batches_done: 3 }) });
  assert.deepEqual(states(steps), ["done", "active", "waiting"]);
  assert.equal(steps[1].detail, "3 of 5 batches received");
  const failed = analysisSteps({ power: { state: "failed" }, modis: modis({ state: "failed" }) });
  assert.deepEqual(states(failed), ["failed", "failed", "waiting"]);
});

test("retries are said in plain words", () => {
  assert.equal(modisLine(modis({ batches_done: 2, attempt: 2 })),
    "2 of 5 batches received. Satellite server busy, trying again (2 of 4)…");
  assert.equal(modisLine({ state: "idle" }), "Asking the satellite server…");
  assert.equal(modisLine(modis({ batches_total: 0 })), "Asking the satellite server…");
});

test("demo fields: answered at once, every step done without waiting", () => {
  const steps = analysisSteps(null, { answered: true, data: { pending: [], failed: [] } });
  assert.deepEqual(states(steps), ["done", "done", "done"]);
});

test("answered while MODIS goes on, or after it failed", () => {
  assert.deepEqual(states(analysisSteps(null, { answered: true, data: { pending: ["ndvi"], failed: [] } })), ["done", "active", "done"]);
  assert.deepEqual(states(analysisSteps(null, { answered: true, data: { pending: [], failed: ["ndvi"] } })), ["done", "failed", "done"]);
});

test("each step change is announced once, not every poll", () => {
  const a = analysisSteps(null);
  assert.equal(announcement(null, a), "NASA weather data (POWER): started. Satellite photos (MODIS): started.");
  const b = analysisSteps({ power: { state: "done" }, modis: modis({ batches_done: 1 }) });
  assert.equal(announcement(a, b), "NASA weather data (POWER): received.");
  const c = analysisSteps({ power: { state: "done" }, modis: modis({ batches_done: 4, attempt: 3 }) });
  assert.equal(announcement(b, c), null, "batch counts and retries are not read out");
  const d = analysisSteps(null, { answered: true, data: { pending: [], failed: ["ndvi"] } });
  assert.equal(announcement(c, d), "Satellite photos (MODIS): didn't arrive. Comparing rotations: done.");
});

test("progress polling stops when MODIS is done or failed, or the farmer leaves", () => {
  const on = { downloading: true, onResults: true };
  assert.equal(shouldPollProgress(null, on), true);
  assert.equal(shouldPollProgress({ modis: modis() }, on), true);
  assert.equal(shouldPollProgress({ modis: { state: "done" } }, on), false);
  assert.equal(shouldPollProgress({ modis: { state: "failed" } }, on), false);
  assert.equal(shouldPollProgress({ modis: modis() }, { downloading: true, onResults: false }), false);
  assert.equal(shouldPollProgress({ modis: modis() }, { downloading: false, onResults: true }), false);
});

test("elapsed time in farmer words", () => {
  assert.equal(formatElapsed(1), "1 second");
  assert.equal(formatElapsed(8.4), "8 seconds");
  assert.equal(formatElapsed(60), "1 min");
  assert.equal(formatElapsed(80), "1 min 20 s");
  assert.equal(formatElapsed(undefined), "0 seconds");
});
