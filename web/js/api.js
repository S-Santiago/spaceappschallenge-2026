// Thin client for the FarmLens API (src/fieldshift/api.py, contract in docs/work-plan.md).
// Every failure becomes an ApiError with a `kind` that format.errorMessage turns into plain English;
// raw server details are never shown to the farmer.

import { errorKind } from "./format.js";

export class ApiError extends Error {
  constructor(kind, status = 0) {
    super(kind);
    this.kind = kind;
    this.status = status;
  }
}

async function request(path, { method = "GET", body, timeoutMs = 20000 } = {}) {
  if (typeof navigator !== "undefined" && navigator.onLine === false) throw new ApiError("offline");
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  let resp;
  try {
    resp = await fetch(path, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal: ctrl.signal,
    });
  } catch (err) {
    if (err?.name === "AbortError") throw new ApiError("timeout");
    throw new ApiError(navigator.onLine === false ? "offline" : "network");
  } finally {
    clearTimeout(timer);
  }
  if (!resp.ok) throw new ApiError(errorKind(resp.status), resp.status);
  try {
    return await resp.json();
  } catch {
    throw new ApiError("server", resp.status);
  }
}

export const getFields = () => request("/api/fields");
export const getCrops = () => request("/api/crops?lang=en");

/** Demo fields answer from pre-loaded data; a new map point may wait for NASA (POWER + MODIS). */
export function analyze(inputs, { freePoint = false } = {}) {
  return request("/api/analyze", { method: "POST", body: inputs, timeoutMs: freePoint ? 75000 : 20000 });
}
