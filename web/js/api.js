// Thin client for the FarmLens API (src/fieldshift/api.py, contract in docs/work-plan.md).
// Every failure becomes an ApiError with a `kind` that format.errorMessage turns into plain English;
// raw server details are never shown to the farmer.

import { analysisKey, errorKind } from "./format.js";

export class ApiError extends Error {
  constructor(kind, status = 0) {
    super(kind);
    this.kind = kind;
    this.status = status;
  }
}

const isOffline = () => typeof navigator !== "undefined" && navigator.onLine === false;

/**
 * JSON from the API plus where it came from. Offline, the request still goes out: the service worker
 * answers from its cache when it can (sw.js), and only a real failure becomes an "offline" ApiError.
 * `saved`: ISO date the cached copy was saved, when the answer came from the cache while offline.
 */
async function send(path, { method = "GET", body, headers = {}, timeoutMs = 20000 } = {}) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  let resp;
  try {
    resp = await fetch(path, {
      method,
      headers: body ? { "Content-Type": "application/json", ...headers } : headers,
      body: body ? JSON.stringify(body) : undefined,
      signal: ctrl.signal,
    });
  } catch (err) {
    if (err?.name === "AbortError") throw new ApiError("timeout");
    throw new ApiError(isOffline() ? "offline" : "network");
  } finally {
    clearTimeout(timer);
  }
  if (!resp.ok) throw new ApiError(errorKind(resp.status), resp.status);
  let data;
  try {
    data = await resp.json();
  } catch {
    throw new ApiError("server", resp.status);
  }
  const savedAt = resp.headers.get("X-FarmLens-Saved-At");
  const fromCache = resp.headers.get("X-FarmLens-Offline") === "1" || (Boolean(savedAt) && isOffline());
  return { data, saved: fromCache ? savedAt || "" : null };
}

const request = async (path, opts) => (await send(path, opts)).data;

export const getFields = () => request("/api/fields");
export const getCrops = () => request("/api/crops?lang=en");

/** Demo fields answer from pre-loaded data; a new map point may wait for NASA (POWER + MODIS). */
export function analyze(inputs, { freePoint = false } = {}) {
  return send("/api/analyze", {
    method: "POST", body: inputs, headers: { "X-FarmLens-Key": analysisKey(inputs) }, timeoutMs: freePoint ? 75000 : 20000,
  });
}

/** Query string for GET /api/predictions from the analysis inputs (field or point, current rotation, slope). */
export function predictionsQuery(inputs) {
  const q = new URLSearchParams();
  if (inputs.field) q.set("field", inputs.field);
  else { q.set("lat", String(inputs.lat)); q.set("lon", String(inputs.lon)); }
  for (const id of inputs.rotation || []) q.append("rotation", id);
  if (inputs.slope) q.set("slope", inputs.slope);
  return q.toString();
}

/**
 * Place search by name with OpenStreetMap Nominatim (map.findPlace keeps only places in Málaga province).
 * One request per tap on "Find", never while typing, as the Nominatim usage policy asks. Network only.
 */
export const searchPlaces = (params) =>
  request(`https://nominatim.openstreetmap.org/search?${params}`, { headers: { Accept: "application/json" }, timeoutMs: 10000 });

/** Statistics over NASA history (P-01, P-02, P-03, P-07). A new point may wait for NASA POWER. */
export function getPredictions(inputs, { freePoint = false } = {}) {
  return send(`/api/predictions?${predictionsQuery(inputs)}`, { timeoutMs: freePoint ? 75000 : 20000 });
}
