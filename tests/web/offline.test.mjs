// Offline support (#40, #14): synthetic cache key for POST /api/analyze and how api.js reports saved answers.
// The service worker itself (web/sw.js) is checked by hand in the browser (airplane mode) and statically by pytest.
import assert from "node:assert/strict";
import { test } from "node:test";

import { analyze, getPredictions } from "../../web/js/api.js";
import { analysisKey, errorMessage } from "../../web/js/format.js";

const BODY = {
  field: "antequera", rotation: ["durum_wheat", "durum_wheat", "sunflower"],
  priorities: { water: 1, soil: 1, income: 1, risk: 1 }, irrigation: "none", slope: "flat", lang: "en",
};

test("analysisKey is the same for the same answers in any key order", () => {
  const shuffled = { lang: "en", slope: "flat", irrigation: "none", priorities: { risk: 1, income: 1, soil: 1, water: 1 },
    rotation: ["durum_wheat", "durum_wheat", "sunflower"], field: "antequera" };
  assert.equal(analysisKey(shuffled), analysisKey(BODY));
  assert.equal(analysisKey({ ...BODY, priorities: { ...BODY.priorities, water: "1" } }), analysisKey(BODY));
});

test("analysisKey changes with any answer, keeps rotation order and rounds points", () => {
  const base = analysisKey(BODY);
  assert.notEqual(analysisKey({ ...BODY, slope: "steep" }), base);
  assert.notEqual(analysisKey({ ...BODY, priorities: { ...BODY.priorities, water: 3 } }), base);
  assert.notEqual(analysisKey({ ...BODY, rotation: ["sunflower", "durum_wheat", "durum_wheat"] }), base);
  const { field, ...rest } = BODY;
  assert.equal(analysisKey({ ...rest, lat: 36.8912, lon: -4.6789 }), analysisKey({ ...rest, lat: 36.89, lon: -4.68 }));
});

function withFetch(handler, online, fn) {
  const realFetch = globalThis.fetch;
  const realNav = Object.getOwnPropertyDescriptor(globalThis, "navigator");
  globalThis.fetch = handler;
  Object.defineProperty(globalThis, "navigator", { value: { onLine: online }, configurable: true });
  return fn().finally(() => {
    globalThis.fetch = realFetch;
    if (realNav) Object.defineProperty(globalThis, "navigator", realNav);
  });
}

const json = (body, headers = {}) => new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json", ...headers } });

test("analyze sends the key and reports a fresh answer as not saved", () => withFetch(async (url, opts) => {
  assert.equal(opts.headers["X-FarmLens-Key"], analysisKey(BODY));
  return json({ ok: 1 });
}, true, async () => {
  assert.deepEqual(await analyze(BODY), { data: { ok: 1 }, saved: null });
}));

test("offline: the request still goes out and a saved answer comes back with its date", () => withFetch(async () =>
  json({ ok: 1 }, { "X-FarmLens-Offline": "1", "X-FarmLens-Saved-At": "2026-11-14T15:40:00.000Z" }), false, async () => {
  assert.deepEqual(await analyze(BODY), { data: { ok: 1 }, saved: "2026-11-14T15:40:00.000Z" });
}));

test("predictions from the cache count as saved only when the phone is offline", async () => {
  const cached = () => json({ period: "2005-2025" }, { "X-FarmLens-Saved-At": "2026-11-14T15:40:00.000Z" });
  await withFetch(async () => cached(), true, async () => {
    assert.equal((await getPredictions(BODY)).saved, null);
  });
  await withFetch(async () => cached(), false, async () => {
    assert.equal((await getPredictions(BODY)).saved, "2026-11-14T15:40:00.000Z");
  });
});

test("offline with nothing saved is a friendly offline error", () => withFetch(async () => { throw new TypeError("Failed to fetch"); }, false, async () => {
  await assert.rejects(analyze(BODY), (err) => err.kind === "offline");
  assert.match(errorMessage("offline").text, /Only results you opened before on this phone work offline/);
}));
