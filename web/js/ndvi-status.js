// Satellite photos (MODIS greenness) status for a new map point: pure logic, no DOM (tests/web/ndvi-status.test.mjs).
// The API answers `pending: ["ndvi"]` while MODIS downloads in the background and `failed: ["ndvi"]` once it failed
// (docs/work-plan.md, "Points that are not demo fields"). The PWA asks again every 30 s, at most 8 times.

export const PENDING_RETRY_MS = 30000;
export const PENDING_TRIES = 8;

const has = (list, item) => Array.isArray(list) && list.includes(item);

/**
 * "downloading" | "failed" | "arrived" | null for an /api/analyze answer.
 * `exhausted`: the PWA stopped asking (tries used up), so nothing is loading any more, so "failed".
 * `arrived`: the photos came in during this visit (a poll turned pending into ready).
 */
export function ndviStatus(data, { exhausted = false, arrived = false } = {}) {
  if (has(data?.failed, "ndvi")) return "failed";
  if (has(data?.pending, "ndvi")) return exhausted ? "failed" : "downloading";
  return arrived ? "arrived" : null;
}

/** Ask the API again only while the photos are downloading and tries are left. */
export function shouldPoll(data, tries) {
  return ndviStatus(data) === "downloading" && tries < PENDING_TRIES;
}

/** Banner for a status: {kind, icon?, title, text, actions} (actions: show "Try again" + "Use a demo field"). */
export function ndviBanner(status) {
  if (status === "downloading") return {
    kind: "warn", title: "Satellite photos are still downloading.",
    text: " They usually take 1–3 minutes, sometimes longer. Rain, heat and frost are ready. Keep this page open.",
    actions: false,
  };
  if (status === "failed") return {
    kind: "warn", title: "Satellite photos didn't arrive for this point.",
    text: " Results use rain, heat and frost only, so bare months are unknown.",
    actions: true,
  };
  if (status === "arrived") return { kind: "ok", icon: "check", title: "Satellite photos added.", text: " Bare months are shown now.", actions: false };
  return null;
}
