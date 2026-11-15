// Satellite photos status for a new map point (web/js/ndvi-status.js). Run: node --test tests/web
import assert from "node:assert/strict";
import { test } from "node:test";

import { PENDING_TRIES, ndviBanner, ndviStatus, shouldPoll } from "../../web/js/ndvi-status.js";

const downloading = { pending: ["ndvi"], failed: [] };
const failed = { pending: [], failed: ["ndvi"] };
const ready = { pending: [], failed: [] };

test("status follows the API fields", () => {
  assert.equal(ndviStatus(downloading), "downloading");
  assert.equal(ndviStatus(failed), "failed");
  assert.equal(ndviStatus(ready), null);
  assert.equal(ndviStatus({ pending: [] }), null, "old API answers without `failed` still work");
  assert.equal(ndviStatus(undefined), null);
});

test("no more tries means nothing is loading: failed, never downloading", () => {
  assert.equal(ndviStatus(downloading, { exhausted: true }), "failed");
  assert.equal(ndviStatus(ready, { exhausted: true }), null);
});

test("arrived only when the photos came in during this visit", () => {
  assert.equal(ndviStatus(ready, { arrived: true }), "arrived");
  assert.equal(ndviStatus(failed, { arrived: true }), "failed");
});

test("polling stops when done, failed or out of tries", () => {
  assert.equal(shouldPoll(downloading, 0), true);
  assert.equal(shouldPoll(downloading, PENDING_TRIES - 1), true);
  assert.equal(shouldPoll(downloading, PENDING_TRIES), false);
  assert.equal(shouldPoll(failed, 0), false);
  assert.equal(shouldPoll(ready, 0), false);
});

test("banner texts make no false promises", () => {
  const d = ndviBanner("downloading");
  assert.match(d.title + d.text, /still downloading.*1–3 minutes, sometimes longer.*Keep this page open/s);
  assert.equal(d.actions, false);
  const f = ndviBanner("failed");
  assert.match(f.title + f.text, /didn't arrive.*rain, heat and frost only.*bare months are unknown/s);
  assert.equal(f.actions, true, "failed offers Try again + example field");
  assert.equal(ndviBanner("arrived").title, "Satellite photos added.");
  assert.equal(ndviBanner("arrived").icon, "check", "confirmation by icon + text, not colour only");
  assert.equal(ndviBanner(null), null);
  for (const s of ["downloading", "failed", "arrived"]) assert.doesNotMatch(ndviBanner(s).text, /1–2 minutes|loading/);
});
