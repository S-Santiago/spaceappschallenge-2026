// What the server is really doing for a new map point (GET /api/progress, docs/work-plan.md "Live progress"),
// as steps the loader and the satellite banner can draw. Pure logic, no DOM and no visual style, so any loader
// design can use it (tests/web/progress-steps.test.mjs).
//
// Step: {id, label, state, detail}; state = "waiting" | "active" | "done" | "failed".

export const PROGRESS_POLL_MS = 2000;

const has = (list, item) => Array.isArray(list) && list.includes(item);

/** "8 seconds", "1 min 20 s". */
export function formatElapsed(seconds) {
  const s = Math.max(0, Math.round(Number(seconds) || 0));
  if (s < 60) return `${s} second${s === 1 ? "" : "s"}`;
  const rest = s % 60;
  return `${Math.floor(s / 60)} min${rest ? ` ${rest} s` : ""}`;
}

/** One plain line for the MODIS download: batches received and, when the server is busy, the try number. */
export function modisLine(m) {
  if (!m || m.state === "idle") return "Asking the satellite server…";
  if (m.state === "done") return "Received";
  if (m.state === "failed") return "Didn't arrive";
  const parts = [m.batches_total ? `${m.batches_done} of ${m.batches_total} batches received` : "Asking the satellite server…"];
  if (m.attempt > 1) parts.push(`Satellite server busy, trying again (${m.attempt} of ${m.attempts_max})…`);
  return parts.join(". ");
}

/**
 * Steps of one analysis. `progress`: last GET /api/progress answer (null before the first one, or for demo fields).
 * `answered`: POST /api/analyze has answered with `data`, so the results are ready.
 */
export function analysisSteps(progress, { answered = false, data = null } = {}) {
  const p = progress || {};
  let power;
  if (answered || p.power?.state === "done") power = ["done", "Received"];
  else if (p.power?.state === "failed") power = ["failed", "Didn't arrive"];
  else power = ["active", "Asking NASA…"];

  let modis;
  if (answered && has(data?.failed, "ndvi")) modis = ["failed", "Didn't arrive. Results use rain, heat and frost only"];
  else if (answered && has(data?.pending, "ndvi")) modis = ["active", "Still downloading. Your results can be shown already"];
  else if (answered) modis = ["done", "Received"];
  else if (p.modis?.state === "done") modis = ["done", "Received"];
  else if (p.modis?.state === "failed") modis = ["failed", "Didn't arrive"];
  else modis = ["active", modisLine(p.modis)];

  const compare = answered ? ["done", "Done"] : ["waiting", ""];
  return [
    { id: "power", label: "NASA weather data (POWER)", state: power[0], detail: power[1] },
    { id: "modis", label: "Satellite photos (MODIS)", state: modis[0], detail: modis[1] },
    { id: "compare", label: "Comparing rotations", state: compare[0], detail: compare[1] },
  ];
}

const SAID = { active: "started", done: "received", failed: "didn't arrive" };

/** Text for the one live region: only the steps whose state changed since `before` (never every poll). */
export function announcement(before, after) {
  const changed = after.filter((s, i) => s.state !== "waiting" && s.state !== before?.[i]?.state);
  if (!changed.length) return null;
  return changed.map((s) => `${s.label}: ${s.id === "compare" && s.state === "done" ? "done" : SAID[s.state]}.`).join(" ");
}

/** Keep asking GET /api/progress while the satellite photos download and the farmer is on the results. */
export function shouldPollProgress(progress, { downloading, onResults }) {
  if (!downloading || !onResults) return false;
  return !["done", "failed"].includes(progress?.modis?.state);
}
