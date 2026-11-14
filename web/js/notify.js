// Heavy-rain warnings on this phone (issue #42). Loaded on demand: with "What to expect" when it shows alert
// months, and at start-up only if warnings are already on. Local notifications only — no push server, no
// subscription; the fields with warnings on and the months already shown are kept in this phone's localStorage
// (docs/architecture.md -> Privacy). Permission is asked only after a tap on the button.

import { esc } from "./format.js";
import { icon, withIcon } from "./icons.js";
import { fromMonth } from "./expect-format.js";
import {
  STORE, dedupeKey, emptyStore, keepAlerts, markSent, pendingWarnings, warnState, warningHash, warningText,
} from "./notify-format.js";

const ICON = "icons/icon-192.png";

function load() {
  try {
    const s = JSON.parse(localStorage.getItem(STORE) || "null");
    return s && typeof s.fields === "object" && Array.isArray(s.sent) ? s : emptyStore();
  } catch { return emptyStore(); }
}

function save(store) {
  try { localStorage.setItem(STORE, JSON.stringify(store)); return true; } catch { return false; }
}

export const watched = (key) => load().fields[key] || null;

export function supported() {
  try {
    return window.isSecureContext && "Notification" in window && "serviceWorker" in navigator &&
      "showNotification" in ServiceWorkerRegistration.prototype;
  } catch { return false; }
}

const permission = () => (supported() ? Notification.permission : "unsupported");

/** The service worker registration, or an error after 5 s (e.g. it never installed). */
function registration() {
  return Promise.race([
    navigator.serviceWorker.ready,
    new Promise((_, reject) => setTimeout(() => reject(new Error("no service worker")), 5000)),
  ]);
}

async function show(text, key, tag, reg) {
  await (reg || await registration()).showNotification(text.title, {
    body: text.body, icon: ICON, tag, lang: "en", data: { hash: warningHash(key) },
  });
}

/** Show the warnings that are due now (this month or next) and not shown before. Never throws: {shown, failed}. */
export async function checkWarnings(today = new Date()) {
  if (permission() !== "granted") return { shown: 0, failed: 0 };
  const store = load();
  const due = pendingWarnings(store, today);
  if (!due.length) return { shown: 0, failed: 0 };
  let reg;
  try { reg = await registration(); } catch { return { shown: 0, failed: due.length }; } // try again next time
  const shown = [];
  for (const w of due) {
    try { await show(warningText(w.name, w.alert), w.key, w.dedupe, reg); shown.push(w.dedupe); } catch { /* next time */ }
  }
  if (shown.length) save(markSent(store, shown, today));
  return { shown: shown.length, failed: due.length - shown.length };
}

/** Keep the stored alerts of a watched field in step with the latest predictions (also the cached ones). */
function refresh(key, field) {
  const store = load();
  if (!store.fields[key]) return;
  store.fields[key] = { ...store.fields[key], ...field };
  save(store);
}

function render(st, field) {
  const why = `<p>We'll remind you on this phone when heavy-rain days often fall while your field is bare. Nothing is sent to us.</p>`;
  if (st === "unsupported") {
    return `<p><strong>${withIcon("bell-off", "Warnings can't be shown on this phone or browser.")}</strong> On Android, open FarmLens in Chrome. On an iPhone, first add FarmLens to the Home Screen (iOS 16.4 or later). The months above stay here to check any time.</p>`;
  }
  if (st === "denied") {
    // Settings steps: a drawn chevron between them, with "then" for screen readers.
    const then = `${icon("chevron-right")}<span class="sr-only">then</span>`;
    const steps = (...names) => names.map((n) => `<strong>${n}</strong>`).join(` ${then} `);
    return `${why}<p style="margin-top:8px"><strong>${withIcon("bell-off", "Warnings are blocked for FarmLens on this phone.")}</strong></p>` +
      `<p style="margin-top:8px">To allow them in Chrome, tap the icon next to the address, or the menu ${icon("more")}<span class="sr-only">(three dots)</span>. ` +
      `Then tap ${steps("Site settings", "Notifications", "Allow")}.</p>` +
      `<p style="margin-top:8px">In the installed app, hold the FarmLens icon. Then tap ${steps("App info", "Notifications")}. Then open this page again.</p>`;
  }
  if (st === "on") {
    return `<p><strong>${withIcon("check", "Warnings on")}</strong> for ${esc(field.name)}. You'll get one reminder for each month above. It comes in the month before, or in that month. FarmLens checks when you open it.</p>
      <div class="actions">
        <button type="button" class="btn btn--block" data-warn="example">Show an example notification</button>
        <button type="button" class="btn btn--block" data-warn="off">Turn off</button>
      </div>`;
  }
  return `${why}<div class="actions"><button type="button" class="btn btn--block" data-warn="on">${withIcon("bell", "Warn me when this risk is near")}</button></div>`;
}

/**
 * Mount the control in the alert card. `field` = {key, name, inputs, alerts}. Returns nothing; all states are
 * explained in words (unsupported, blocked, on, off), so there is never a button that does nothing.
 */
export function mountWarn(slot, field, today = new Date()) {
  const alerts = keepAlerts(field.alerts);
  if (!slot || !field.key || !alerts.length) return;
  const entry = { name: field.name, inputs: field.inputs, alerts };
  if (watched(field.key)) {
    refresh(field.key, entry);
    checkWarnings(today);
  }
  const status = (text) => `<p class="small warn-status" role="status">${esc(text)}</p>`;
  const draw = (note = "") => {
    const st = warnState({ supported: supported(), permission: permission(), watched: Boolean(watched(field.key)) });
    slot.innerHTML = `<h4 class="sub">${withIcon("bell", "Warnings on this phone")}</h4>${render(st, field)}${note ? status(note) : ""}`;
    slot.hidden = false;
  };
  slot.addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-warn]");
    if (!btn) return;
    const what = btn.dataset.warn;
    if (what === "on") {
      btn.disabled = true;
      let result = permission();
      try { if (result === "default") result = await Notification.requestPermission(); } catch { result = permission(); }
      if (result !== "granted") { draw(result === "denied" ? "" : "Warnings were not turned on. Tap the button again to allow them."); return; }
      const store = load();
      store.fields[field.key] = entry;
      if (!save(store)) { draw("This phone could not save the setting (storage is full or blocked), so warnings stay off."); return; }
      draw("Turning warnings on…");
      const { shown, failed } = await checkWarnings(today);
      draw(failed ? "Warnings on, but this phone could not show a warning just now. FarmLens will try again next time you open it."
        : shown ? "Warnings on. A warning for a month that is near was just shown."
          : "Warnings on. Nothing is near yet: you'll get a warning when an alert month comes close.");
    } else if (what === "off") {
      const store = load();
      delete store.fields[field.key];
      store.sent = store.sent.filter((k) => !k.startsWith(`${field.key}|`));
      save(store);
      draw("Warnings off for this field. You can turn them on again here.");
    } else if (what === "example") {
      const next = fromMonth(alerts, today.getMonth() + 1)[0]; // the next alert month (this month counts)
      try {
        await show(warningText(field.name, next, { example: true }), field.key, dedupeKey(field.key, "example"));
        draw("Example shown. Look at the top of your screen.");
      } catch {
        draw("The example could not be shown. Close and open FarmLens, then try again.");
      }
    }
  });
  draw();
}
