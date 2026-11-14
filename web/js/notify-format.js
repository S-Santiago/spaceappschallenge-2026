// Pure helpers for heavy-rain warnings on this phone (issue #42). No DOM, no storage, no network, so
// `node --test tests/web` can check them. Local notifications only: nothing is sent to a server.
// Rule (P-07, docs/indicators.md): for each field with warnings on, if alerts[] has the current month or the next
// one, show one notification for that field and month. Dedupe key: "<field key>|YYYY-MM" of the alerted month.

import { MONTHS, num } from "./format.js";
import { count } from "./expect-format.js";

export const STORE = "farmlens-warnings-v1"; // localStorage key (see docs/architecture.md -> Privacy)
export const HASH_PREFIX = "#/warning/";
const LEVEL_WORD = { high: "High", medium: "Medium" };
const KEEP_SENT_MONTHS = 13; // older dedupe keys can never match again

export const emptyStore = () => ({ fields: {}, sent: [] });

/** Where the field is, without the farmer's answers: a demo field slug or the point rounded to ~1 km. */
export function fieldKey(inputs) {
  if (inputs?.field) return `field:${inputs.field}`;
  const lat = num(inputs?.lat), lon = num(inputs?.lon);
  return lat === null || lon === null ? null : `point:${lat.toFixed(2)},${lon.toFixed(2)}`;
}

/** "2026-11" for year 2026, month 11. */
export function monthKey(year, month) {
  return `${year}-${String(month).padStart(2, "0")}`;
}

export const dedupeKey = (key, ym) => `${key}|${ym}`;

/** Only what the warning needs from P-07: month, share of years, years, level. */
export function keepAlerts(alerts) {
  if (!Array.isArray(alerts)) return [];
  return alerts.filter((a) => a && LEVEL_WORD[a.level] && a.month >= 1 && a.month <= 12)
    .map((a) => ({ month: a.month, prob: num(a.prob), years: num(a.years), level: a.level }));
}

/** Alerts for this month and next month (wrapping over New Year), with the YYYY-MM of the alerted month. */
export function dueAlerts(alerts, today = new Date()) {
  const y = today.getFullYear(), m = today.getMonth() + 1;
  const next = m === 12 ? [y + 1, 1] : [y, m + 1];
  return [[y, m], next].flatMap(([year, month]) =>
    keepAlerts(alerts).filter((a) => a.month === month).map((a) => ({ ...a, ym: monthKey(year, month) })));
}

/** Notifications still to show: due alerts of every watched field whose dedupe key is not in `sent`. */
export function pendingWarnings(store, today = new Date()) {
  const sent = new Set(store?.sent || []);
  return Object.entries(store?.fields || {}).flatMap(([key, f]) =>
    dueAlerts(f?.alerts, today)
      .map((alert) => ({ key, name: f.name, alert, dedupe: dedupeKey(key, alert.ym) }))
      .filter((w) => !sent.has(w.dedupe)));
}

/** Add dedupe keys and drop the ones older than about a year. */
export function markSent(store, keys, today = new Date()) {
  const oldest = new Date(today.getFullYear(), today.getMonth() - KEEP_SENT_MONTHS, 1);
  const minYm = monthKey(oldest.getFullYear(), oldest.getMonth() + 1);
  const sent = [...new Set([...(store?.sent || []), ...keys])].filter((k) => (k.split("|").pop() || "") >= minYm);
  return { ...store, sent };
}

/**
 * Notification text in the P-07 wording (docs/indicators.md): a proxy ("heavy-rain days often fall while your
 * field is bare"), counts of years, and "not a forecast". `example` marks the demo button's notification.
 */
export function warningText(name, alert, { example = false } = {}) {
  if (!alert || !LEVEL_WORD[alert.level] || !(alert.month >= 1 && alert.month <= 12)) return null;
  const n = count(alert.prob, alert.years);
  const freq = n === null ? "" : ` (${n} of ${alert.years} years)`;
  const field = String(name || "").trim() || "your field";
  return {
    title: `${example ? "Example: " : ""}Heavy-rain risk on bare soil — ${field}`,
    body: `${LEVEL_WORD[alert.level]} risk in ${MONTHS[alert.month - 1]}: heavy rain often falls on bare soil${freq}. ` +
      "Keep stubble or a cover crop. Past NASA data, not a forecast.",
  };
}

/** Link the notification opens: What to expect for that field (the page resolves the key from local storage). */
export const warningHash = (key) => `${HASH_PREFIX}${encodeURIComponent(key)}`;

/**
 * Which state the warning control shows: "unsupported" (no notifications here: iPhone Safari not added to the Home
 * Screen, iOS < 16.4, an insecure address…), "denied", "on" (allowed and on for this field) or "off".
 */
export function warnState({ supported, permission, watched }) {
  if (!supported) return "unsupported";
  if (permission === "denied") return "denied";
  return permission === "granted" && watched ? "on" : "off";
}
