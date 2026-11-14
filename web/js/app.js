// FarmLens PWA (decision 0005: vanilla JS, no build). Screens with a tiny hash router:
//   #/          the 4-step form (field -> current rotation -> priorities -> farm)
//   #/results   tab "Rotation options": the answer from POST /api/analyze (real engine; no mock data anywhere)
//   #/expect    tab "What to expect": GET /api/predictions (statistics over NASA history), view loaded on demand

import * as api from "./api.js";
import {
  FIELD_LIMIT_ROWS, MONTH_ABBR, MONTHS, cropName, errorMessage, esc, fmt, fmtCoords, formatDate, keyFacts,
  levelText, limitsDetails, ndviMissing, num, plainEvidence, trendFacts,
} from "./format.js";
import { icon, withIcon } from "./icons.js";
import { findPlace, inMalaga, mountMap, roundPoint } from "./map.js";

const app = document.getElementById("app");

// Example answers per demo field, from the personas in docs/challenge.md. The farmer can change them all.
const PRESETS = {
  antequera: { rotation: ["durum_wheat", "durum_wheat", "sunflower"], irrigation: "none", slope: "flat" },
  campillos: { rotation: ["durum_wheat", "sunflower"], irrigation: "none", slope: "moderate" },
  guadalhorce: { rotation: ["maize", "alfalfa", "faba_bean"], irrigation: "full", slope: "flat" },
};
const DEFAULT_PRESET = { rotation: ["durum_wheat", "durum_wheat", "sunflower"], irrigation: "none", slope: "flat" };
const DEMO_ORDER = ["antequera", "guadalhorce", "campillos"];

const PRIORITIES = [
  ["water", "drop", "Save water"],
  ["soil", "sprout", "Soil health"],
  ["income", "coins", "Income"],
  ["risk", "shield", "Less weather risk"],
];
const PRIORITY_WORDS = ["Not important", "A little", "Important", "Very important"];
const STEP_TITLES = ["Where is your field?", "What do you grow now?", "What matters most to you?", "Your farm"];
const IRRIGATION = [
  ["none", "No irrigation", "Rain only"],
  ["supplementary", "A little", "A few waterings in dry spells"],
  ["full", "Full", "Irrigated all season"],
];
const SLOPE = [
  ["flat", "Flat", "Rain soaks in"],
  ["moderate", "Gentle slope", "Some water runs off in heavy rain"],
  ["steep", "Steep", "Soil washes away in storms"],
];
const SCORE_ROWS = [
  ["water", "drop", "Water"],
  ["soil", "sprout", "Soil health"],
  ["income", "coins", "Income (rough guide only)"],
  ["risk", "shield", "Weather risk (higher = safer)"],
];
const FAMILY_LABEL = { cereal: "Cereal", legume: "Legume", oilseed: "Oilseed", forage: "Forage", cover: "Cover crop", fallow: "Fallow", other: "Other" };
const STAGES = ["Getting NASA data…", "Checking satellite photos of your field…", "Comparing rotations…"];
const LITTLE_COVER_NDVI = 0.35; // calendar word "Little cover" between Bare (<0.25) and Green (docs/indicators.md I-09)

const state = {
  fields: [], crops: [], names: {}, types: {},
  field: null, point: null, mapApi: null,
  rotation: [], priorities: { water: 1, soil: 1, income: 1, risk: 1 }, irrigation: "none", slope: "flat",
  edited: false, busy: false, result: null, step: 1,
  predictions: null, // {key, data} for the current analysis inputs
};
const TABS = [["results", "Rotation options"], ["expect", "What to expect"]];

// ------------------------------------------------------------------ helpers

const $ = (sel, root = app) => root.querySelector(sel);
const familyOf = (id) => (id === "fallow" ? "fallow" : state.types[id] || "other");
const isFreePoint = () => state.field === "map";
const fieldInfo = () => state.fields.find((f) => f.slug === state.field);

function applyPreset(slug) {
  const p = PRESETS[slug] || DEFAULT_PRESET;
  const known = p.rotation.filter((id) => state.names[id]);
  state.rotation = known.length ? known : [state.crops[0]?.id].filter(Boolean);
  state.irrigation = p.irrigation;
  state.slope = p.slope;
}

function inputs() {
  const where = isFreePoint() ? { lat: state.point.lat, lon: state.point.lon } : { field: state.field };
  return { ...where, rotation: [...state.rotation], priorities: { ...state.priorities }, irrigation: state.irrigation, slope: state.slope, lang: "en" };
}

function strip(years, label) {
  const plots = years.map((id, i) =>
    `<div class="plot f-${familyOf(id)}"><span class="yr">Year ${i + 1}</span><span class="crop">${esc(cropName(id, state.names))}</span></div>`).join("");
  const fams = [...new Set(years.map(familyOf))];
  const key = fams.map((f) => `<span><i class="f-${f}" aria-hidden="true"></i>${FAMILY_LABEL[f]}</span>`).join("");
  return `<div class="strip" role="img" aria-label="${esc(label)}: ${esc(years.map((id, i) => `year ${i + 1} ${cropName(id, state.names)}`).join(", "))}">${plots}</div>` +
    `<div class="key" aria-hidden="true">${key}</div>`;
}

/** Crop names in order with a drawn arrow between them ("then" for screen readers). */
function sequence(ids) {
  const sep = ` ${icon("next")}<span class="sr-only">then</span> `;
  return ids.map((id) => esc(cropName(id, state.names))).join(sep);
}

function radioCards(name, options, current) {
  return `<div class="choices">${options.map(([value, title, hint]) => `
    <label class="choice"><input type="radio" name="${name}" value="${esc(value)}"${value === current ? " checked" : ""}>
      <span><strong>${esc(title)}</strong><span class="small muted">${esc(hint)}</span></span></label>`).join("")}</div>`;
}

// One step on screen at a time (UX launch route 02): "Step N of 4" in large type, then Next / Back.
const STEP_COUNT = 4;

function stepTitle(n, title) {
  return `<h2 class="step-title" id="s${n}" tabindex="-1">${esc(title)}</h2>`;
}

function stepper(n) {
  return `<p class="step-count">Step ${n} of ${STEP_COUNT}</p>
    <ol class="dots" aria-hidden="true">${Array.from({ length: STEP_COUNT }, (_, i) =>
    `<li class="${i + 1 < n ? "done" : i + 1 === n ? "now" : ""}"></li>`).join("")}</ol>`;
}

// One primary action per step: Next, and on the last step "Analyze my field". The example answers are filled in,
// so "Analyze now" on steps 1-3 is a quiet shortcut for a farmer who doesn't want to change anything.
function stepMain(n) {
  return n < STEP_COUNT
    ? `<button type="button" class="btn btn--primary" data-next>${withIcon("next", "Next")}</button>`
    : `<button type="submit" class="btn btn--primary js-analyze" id="go" data-label="Analyze my field">Analyze my field</button>`;
}

function stepNav(n) {
  const back = n > 1 ? `<button type="button" class="btn btn--secondary" data-back>${withIcon("back", "Back")}</button>` : "";
  const quick = n < STEP_COUNT
    ? `<button type="submit" class="btn btn--quiet js-analyze" data-label="Analyze now with these answers">Analyze now with these answers</button>` : "";
  return back + quick;
}

const BANNER_ICON = { error: "warning", warn: "warning", ok: "info" };

function banner(kind, title, text, actions = "") {
  return `<div class="banner banner--${kind}" role="${kind === "error" ? "alert" : "status"}">${icon(BANNER_ICON[kind] || "info")}` +
    `<div><strong>${esc(title)}</strong>${esc(text)}${actions}</div></div>`;
}

// ------------------------------------------------------------------ boot

async function boot() {
  app.innerHTML = `<p class="muted" role="status">Loading FarmLens…</p>`;
  try {
    // One after the other: on a fresh server the first DB access builds the database (db.init_db),
    // and two parallel first requests can collide there.
    const fields = await api.getFields();
    const crops = await api.getCrops();
    state.fields = DEMO_ORDER.map((s) => fields.find((f) => f.slug === s)).filter(Boolean)
      .concat(fields.filter((f) => !DEMO_ORDER.includes(f.slug)));
    state.crops = crops;
    state.names = Object.fromEntries(crops.map((c) => [c.id, c.name]));
    state.types = Object.fromEntries(crops.map((c) => [c.id, c.type]));
  } catch (err) {
    const msg = errorMessage(err.kind);
    app.innerHTML = masthead() + banner("error", msg.title, ` ${msg.text}`,
      `<div class="actions"><button class="btn btn--primary" id="retry-boot">Try again</button></div>`);
    $("#retry-boot").addEventListener("click", boot);
    return;
  }
  if (!state.crops.length) {
    app.innerHTML = masthead() + banner("error", "We couldn't load the crop list.", " Try again in 1 minute.",
      `<div class="actions"><button class="btn btn--primary" id="retry-boot">Try again</button></div>`);
    $("#retry-boot").addEventListener("click", boot);
    return;
  }
  state.field = state.fields[0]?.slug || "map";
  applyPreset(state.field);
  route();
}

// The logo is the app icon (icons/icon.svg): one cached file, colours from the palette there.
function masthead() {
  return `<header class="masthead">
    <div class="brand"><img src="icons/icon.svg" width="32" height="32" alt="">
    <h1>FarmLens</h1></div>
    <p class="lead">Compare crop rotations for <strong>your field</strong>. We use 21 years of NASA weather and satellite data. Example answers are filled in. Answer 4 short steps, then tap <strong>Analyze my field</strong>.</p>
  </header>`;
}

// ------------------------------------------------------------------ form screen

function renderForm() {
  const fieldOptions = state.fields.map((f) => [f.slug, f.name, f.description]);
  fieldOptions.push(["map", "Another point on the map", "Search your town or tap the map. Málaga only. Needs internet."]);
  const step = (n, body) => `<section class="step" data-step="${n}" aria-labelledby="s${n}"${n === state.step ? "" : " hidden"}>
      ${stepTitle(n, STEP_TITLES[n - 1])}${body}</section>`;
  app.innerHTML = `${masthead()}
  <form id="form" novalidate>
    <div class="stepper" id="stepper">${stepper(state.step)}</div>
    ${step(1, `
      <fieldset><legend>Pick an example field or a point on the map</legend>${radioCards("field", fieldOptions, state.field)}</fieldset>
      <div id="map-box" ${isFreePoint() ? "" : "hidden"}>
        <p class="small" style="margin-top:12px">Only fields in Málaga province. Type your town, tap your field on the map, or use your location.</p>
        <div class="place-search" role="search">
          <label for="place" class="sr-only">Town or area in Málaga province</label>
          <input id="place" type="search" autocomplete="off" enterkeyhint="search" placeholder="Town or area, e.g. Antequera" aria-describedby="where">
          <button type="button" class="btn" id="find">Find</button>
        </div>
        <div class="map" id="map" aria-label="Map of Málaga province. Tap inside the border to choose your field."></div>
        <div class="actions"><button type="button" class="btn btn--block" id="locate">${withIcon("pin", "Use my location")}</button></div>
      </div>
      <div class="location" id="where" aria-live="polite"></div>`)}
    ${step(2, `
      <p class="small" id="preset-note"></p>
      <fieldset class="gap-top"><legend>After how many years do you grow the same crop again?</legend>
        <div class="segmented">${[1, 2, 3, 4].map((n) => `<label><input type="radio" name="years" value="${n}"${n === state.rotation.length ? " checked" : ""}><span>${n} ${n === 1 ? "year" : "years"}</span></label>`).join("")}</div>
      </fieldset>
      <div id="years" class="gap-top">${yearRows()}</div>
      <div id="strip" class="gap-top">${strip(state.rotation, "Your current rotation")}</div>`)}
    ${step(3, `
      <p class="small">Tap one answer for each.</p>
      <div class="gap-top">${PRIORITIES.map(([k, name, label]) => `
        <fieldset class="prio"><legend>${withIcon(name, esc(label))}</legend>
          <div class="segmented segmented--grid">${PRIORITY_WORDS.map((word, v) => `<label><input type="radio" name="p-${k}" value="${v}"${v === state.priorities[k] ? " checked" : ""}><span>${word}</span></label>`).join("")}</div>
        </fieldset>`).join("")}</div>`)}
    ${step(4, `
      <fieldset><legend>Can you water the field, apart from rain?</legend>${radioCards("irrigation", IRRIGATION, state.irrigation)}</fieldset>
      <fieldset class="gap-top"><legend>Slope of the field</legend>${radioCards("slope", SLOPE, state.slope)}</fieldset>`)}
    <div id="feedback" aria-live="polite"></div>
    <div class="step-main" id="step-main">${stepMain(state.step)}</div>
    <div class="step-nav" id="step-nav">${stepNav(state.step)}</div>
  </form>`;

  $(".masthead .lead").hidden = state.step !== 1;
  updateWhere();
  const form = $("#form");
  form.addEventListener("change", onChange);
  form.addEventListener("submit", (e) => { e.preventDefault(); runAnalysis(); });
  form.addEventListener("click", (e) => {
    if (e.target.closest("[data-next]")) nextStep();
    else if (e.target.closest("[data-back]")) goStep(state.step - 1);
  });
  $("#locate").addEventListener("click", locate);
  $("#find").addEventListener("click", searchPlace);
  // Enter in the search box searches instead of submitting the whole form.
  $("#place").addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); searchPlace(); } });
  if (isFreePoint()) openMap();
}

/** Type a town or area -> the point moves there, only if it is in Málaga province (map.findPlace checks it). */
async function searchPlace() {
  const input = $("#place");
  const where = $("#where");
  const q = input.value.trim();
  if (!q) { input.focus(); return; }
  const find = $("#find");
  find.disabled = true;
  where.innerHTML = `<span class="muted">Looking for “${esc(q)}” in Málaga province…</span>`;
  try {
    const place = await findPlace(q);
    if (!place) {
      where.innerHTML = `<span>We couldn't find “${esc(q)}” in Málaga province. Only places in Málaga can be chosen. Check the spelling, or try the nearest town.</span>`;
      return;
    }
    state.point = place;
    state.mapApi?.setPoint(place, true);
    $("#feedback").innerHTML = "";
    updateWhere();
  } catch {
    where.innerHTML = `<span>The search needs a connection. Try again, or tap the map instead.</span>`;
  } finally {
    find.disabled = false;
  }
}

function updateWhere() {
  const where = $("#where");
  const note = $("#preset-note");
  if (isFreePoint()) {
    if (!state.point) {
      where.innerHTML = `<span class="muted">No point chosen yet. Search your town or tap the map to choose your field.</span>`;
    } else {
      const name = state.point.name ? `<strong>${esc(state.point.name)}</strong> · ` : "";
      where.innerHTML = `${withIcon("pin", `Your point: ${name}<strong>${fmtCoords(state.point.lat, state.point.lon)}</strong>`)}
        <br><span class="small muted">${state.point.name ? "Tap the map to move the point onto your field. " : ""}A new place takes up to 1 minute the first time.</span>`;
    }
    note.textContent = "Example rotation filled in. Change it to match your field.";
  } else {
    const f = fieldInfo();
    where.innerHTML = f ? withIcon("pin", `<strong>${esc(f.name)}</strong> · ${fmtCoords(f.lat, f.lon)} · ${fmt(f.elevation_m, 0, "m")} above sea level`) : "";
    note.textContent = state.edited ? "" : "Example rotation for this area filled in. Change it to match your field.";
  }
}

// One native list per year (no typing: the phone's own picker), crops grouped by family in A-Z order.
function cropSelectOptions(current) {
  const groups = Object.entries(FAMILY_LABEL).map(([fam, label]) => {
    const crops = state.crops.filter((c) => familyOf(c.id) === fam).sort((a, b) => a.name.localeCompare(b.name));
    return crops.length ? `<optgroup label="${esc(label)}">${crops.map((c) =>
      `<option value="${esc(c.id)}"${c.id === current ? " selected" : ""}>${esc(c.name)}</option>`).join("")}</optgroup>` : "";
  });
  return groups.join("");
}

function yearRows() {
  return state.rotation.map((id, i) => `
    <div class="year-row"><label for="y${i}">Year ${i + 1}</label>
      <div class="select-wrap"><select id="y${i}" class="crop-select" data-year="${i}">${cropSelectOptions(id)}</select></div></div>`).join("");
}

// ------------------------------------------------------------------ steps

function goStep(n) {
  const to = Math.max(1, Math.min(STEP_COUNT, n));
  const hash = to === 1 ? "#/" : `#/step/${to}`;
  if (location.hash === hash || (to === 1 && !location.hash)) showStep(to);
  else location.hash = hash; // route() shows it, and the phone's Back button walks back through the steps
}

/** Swap the visible step in place (the map and the answers stay as they are), then focus its title. */
function showStep(n) {
  state.step = n;
  app.querySelectorAll(".step[data-step]").forEach((s) => { s.hidden = Number(s.dataset.step) !== n; });
  $("#stepper").innerHTML = stepper(n);
  $(".masthead .lead").hidden = n !== 1; // what FarmLens is: on the first screen only
  $("#step-main").innerHTML = stepMain(n);
  $("#step-main").hidden = false;
  $("#step-nav").innerHTML = stepNav(n);
  $("#feedback").innerHTML = "";
  if (n === 1 && isFreePoint()) openMap();
  window.scrollTo(0, 0);
  $(`#s${n}`).focus({ preventScroll: true });
}

/** Feedback appears under the button that caused it; bring it into view above the sticky bar. */
function reveal(el) {
  el?.scrollIntoView({ block: "center", behavior: "auto" });
}

function nextStep() {
  if (state.step === 1 && isFreePoint() && !state.point) {
    $("#feedback").innerHTML = banner("error", "Choose your field first.", " Search your town or tap the map. Or pick an example field.");
    reveal($("#feedback"));
    return;
  }
  goStep(state.step + 1);
}

function renderYears() {
  $("#years").innerHTML = yearRows();
  $("#strip").innerHTML = strip(state.rotation, "Your current rotation");
  app.querySelectorAll('input[name="years"]').forEach((r) => { r.checked = Number(r.value) === state.rotation.length; });
}

function onChange(e) {
  const t = e.target;
  $("#feedback").innerHTML = "";
  $("#step-main").hidden = false;
  if (t.name === "field") {
    state.field = t.value;
    if (!state.edited) {
      applyPreset(t.value);
      renderYears();
      app.querySelector(`input[name="irrigation"][value="${state.irrigation}"]`).checked = true;
      app.querySelector(`input[name="slope"][value="${state.slope}"]`).checked = true;
    }
    $("#map-box").hidden = !isFreePoint();
    if (isFreePoint()) openMap();
    updateWhere();
  } else if (t.name === "years") {
    const n = Number(t.value);
    const last = state.rotation.at(-1) || state.crops[0].id;
    state.rotation = Array.from({ length: n }, (_, i) => state.rotation[i] || last);
    state.edited = true;
    renderYears();
    updateWhere();
  } else if (t.dataset.year !== undefined) {
    state.rotation[Number(t.dataset.year)] = t.value;
    state.edited = true;
    $("#strip").innerHTML = strip(state.rotation, "Your current rotation");
    updateWhere();
  } else if (t.name.startsWith("p-")) {
    state.priorities[t.name.slice(2)] = Number(t.value);
  } else if (t.name === "irrigation" || t.name === "slope") {
    state[t.name] = t.value;
    state.edited = true;
  }
}

async function openMap() {
  if (state.mapApi) return;
  const el = $("#map");
  el.innerHTML = `<p class="small muted" style="padding:16px">Loading the map…</p>`;
  try {
    el.innerHTML = "";
    state.mapApi = await mountMap(el, state.point, (p) => { state.point = p; updateWhere(); $("#feedback").innerHTML = ""; });
  } catch {
    el.innerHTML = `<p class="small" style="padding:16px">The map could not load. Check your connection, or tap <strong>Use my location</strong>.</p>`;
  }
}

function locate() {
  const where = $("#where");
  if (!navigator.geolocation) {
    where.innerHTML = `<span>Your phone can't share its location here. Tap the map instead.</span>`;
    return;
  }
  where.innerHTML = `<span class="muted">Finding your location…</span>`;
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const p = roundPoint(pos.coords.latitude, pos.coords.longitude);
      if (!inMalaga(p)) {
        where.innerHTML = `<span>You are outside Málaga province, so your location can't be used. Only fields in Málaga can be chosen: search your town or tap the map.</span>`;
        return;
      }
      state.point = p;
      state.mapApi?.setPoint(state.point, true);
      updateWhere();
    },
    () => { where.innerHTML = `<span>We couldn't get your location. Allow location for this site, or tap the map instead.</span>`; },
    { enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 },
  );
}

// ------------------------------------------------------------------ analysis

async function runAnalysis(next = "#/results") {
  if (state.busy) return;
  const feedback = $("#feedback");
  if (isFreePoint() && !state.point) {
    goStep(1);
    $("#feedback").innerHTML = banner("error", "Choose your field first.", " Search your town or tap the map. Or pick an example field.");
    reveal($("#feedback"));
    return;
  }
  const free = isFreePoint();
  $("#step-main").hidden = false;
  const buttons = [...app.querySelectorAll(".js-analyze, [data-next], [data-back]")];
  state.busy = true;
  buttons.forEach((b) => { b.disabled = true; });
  app.querySelectorAll(".js-analyze").forEach((b) => { b.textContent = "Analyzing…"; });
  feedback.innerHTML = `<div class="progress" role="status"><ol class="stages">${STAGES.map((s) => `<li><span class="mark" aria-hidden="true">·</span>${s}</li>`).join("")}</ol><p class="small muted" id="elapsed"></p></div>`;
  reveal(feedback);
  const items = [...feedback.querySelectorAll(".stages li")];
  const setStage = (i) => items.forEach((li, j) => {
    li.className = j < i ? "done" : j === i ? "active" : "";
    li.querySelector(".mark").innerHTML = j < i ? icon("check") : j === i ? '<span class="spin"></span>' : "·";
  });
  // The API does the three stages in one request (POWER, then MODIS, then the rotation engine), so the list
  // follows the typical timing: POWER answers in ~2 s, MODIS is the slow one for a new point.
  setStage(0);
  const started = Date.now();
  const tick = setInterval(() => {
    const s = Math.round((Date.now() - started) / 1000);
    if (s >= 2) setStage(1);
    const el = $("#elapsed");
    if (el && s >= 5) el.textContent = `${s} seconds · ${free ? "A new place takes up to 1 minute the first time." : "Still working…"}`;
  }, 500);

  const body = inputs();
  try {
    const { data, saved } = await api.analyze(body, { freePoint: free });
    setStage(2);
    state.result = { data, inputs: body, at: saved || new Date().toISOString(), saved: saved !== null, label: free ? `your point (${fmtCoords(body.lat, body.lon)})` : fieldInfo()?.name || "your field" };
    watchPending(state.result);
    setStage(3);
    location.hash = next;
  } catch (err) {
    const msg = errorMessage(err.kind || "server", { freePoint: free });
    feedback.innerHTML = banner("error", msg.title, ` ${msg.text}`,
      `<div class="actions"><button type="button" class="btn btn--primary" id="retry">Try again</button>${
        free && state.fields.length ? `<button type="button" class="btn btn--block" id="use-demo">Use an example field</button>` : ""}</div>`);
    $("#step-main").hidden = true; // "Try again" is the one primary action while the error shows
    reveal(feedback);
    $("#retry").focus({ preventScroll: true });
    $("#retry").addEventListener("click", () => runAnalysis(next));
    $("#use-demo")?.addEventListener("click", () => {
      const first = app.querySelector(`input[name="field"][value="${state.fields[0].slug}"]`);
      first.checked = true;
      first.dispatchEvent(new Event("change", { bubbles: true }));
      goStep(1);
    });
  } finally {
    clearInterval(tick);
    state.busy = false;
    buttons.forEach((b) => {
      if (!b.isConnected) return;
      b.disabled = false;
      if (b.dataset.label) b.textContent = b.dataset.label;
    });
  }
}

// A new map point can come back with `pending: ["ndvi"]`: the API answered from NASA POWER while the slow
// MODIS greenness download goes on in the background (docs/work-plan.md, "Points that are not demo fields").
// Ask again quietly every 30 s (up to 4 min) and redraw the results when the greenness has arrived.
const PENDING_RETRY_MS = 30000;
const PENDING_TRIES = 8;

function isPending(result) {
  return (result?.data?.pending || []).includes("ndvi");
}

function watchPending(result, tries = 0) {
  if (!isPending(result) || tries >= PENDING_TRIES) return;
  setTimeout(async () => {
    if (state.result !== result) return; // a newer analysis replaced this one
    try {
      const { data, saved } = await api.analyze(result.inputs, { freePoint: true });
      if (state.result !== result || saved !== null) return; // offline: keep what we have
      result.data = data;
      if (!isPending(result) && location.hash === "#/results") renderResults();
      if (!isPending(result)) state.predictions = null; // bare months known now: alerts may change
    } catch { /* keep the results we have; try again below */ }
    watchPending(result, tries + 1);
  }, PENDING_RETRY_MS);
}

// ------------------------------------------------------------------ results screen

// Level key for the bar colour (the level word is always printed next to it, so colour is never the only cue).
function levelKey(label, value) {
  if (label === "good" || label === "poor") return label;
  if (label === "neutral" || label === "fair") return "fair";
  const n = num(value);
  return n === null ? "fair" : n >= 67 ? "good" : n >= 34 ? "fair" : "poor";
}

/** A level everywhere a score shows: word + bar + number (DESIGN.md "Level meter"; colour is never the only cue). */
function meter(value, label) {
  const n = Math.max(0, Math.min(100, num(value) ?? 0));
  return `<div class="meter meter--${levelKey(label, value)}"><span class="meter-word">${levelText(label, value)}</span>` +
    `<span class="bar" aria-hidden="true"><i style="width:${n}%"></i></span><span class="meter-num">${fmt(value)}/100</span></div>`;
}

function renderResults(tab = "results") {
  const { data, label, at, inputs: used } = state.result;
  const profile = data?.profile || {};
  const strategies = Array.isArray(data?.strategies) ? data.strategies : [];
  const weights = PRIORITIES.every(([k]) => !used.priorities[k])
    ? "all your priorities are 0, so they count the same" // rotations.overall() falls back to equal weights
    : PRIORITIES.map(([k, , l]) => `${l} ${used.priorities[k]}`).join(" · ");
  const loadingNdvi = isPending(state.result);
  const noNdvi = ndviMissing(profile);

  // DESIGN.md "Tags": only the alternative with the highest overall score gets "Best match for your priorities".
  const alternatives = strategies.filter((s) => s.id !== "current" && num(s.scores?.overall) !== null);
  const bestId = alternatives.length ? alternatives.reduce((a, b) => (num(b.scores.overall) > num(a.scores.overall) ? b : a)).id : null;
  const bestTag = `<span class="tag">Best match for your priorities</span>`;

  const nameOf = (s) => (s.id === "current" ? "Your current rotation" : s.name || "Rotation option");
  const seqOf = (s) => `${sequence(s.years || [])}${s.cover_crop ? ` + ${esc(cropName(s.cover_crop.crop, state.names))}` : ""}`;
  const compare = strategies.length ? `<ul class="compare">${strategies.map((s) => `
      <li${s.id === bestId ? ' class="is-best"' : ""}>${s.id === bestId ? bestTag : ""}<p class="row">${esc(nameOf(s))}</p>
        <p class="small seq">${seqOf(s)}</p>
        ${meter(s.scores?.overall, s.labels?.overall)}</li>`).join("")}</ul>`
    : banner("warn", "We couldn't build rotation options for this field.", " Check your answers and try again, or try an example field.");

  // The answer first (UX: results headline), then the comparison, then each option's evidence under "More detail".
  const best = strategies.find((s) => s.id === bestId);
  const current = strategies.find((s) => s.id === "current");
  const answer = best ? `<section class="answer" aria-labelledby="h-answer">
      <h2 id="h-answer">Best match for your priorities: ${esc(best.name || "Rotation option")}</h2>
      <p class="seq">${seqOf(best)}</p>
      ${meter(best.scores?.overall, best.labels?.overall)}
      <p>${esc(plainEvidence(best.why || "").text)}</p>
      ${current ? `<p class="small">Your current rotation: ${levelText(current.labels?.overall, current.scores?.overall)}, ${fmt(current.scores?.overall)}/100.</p>` : ""}
      <p class="small">An idea to talk over with your adviser. You decide.</p>
      <div class="actions"><button type="button" class="btn btn--primary" data-goto="c-${esc(best.id)}">See why and the risks</button></div>
    </section>`
    : strategies.length ? banner("ok", "Your current rotation is shown below.", " We found no other option that fits your answers better. Try other priorities.") : "";

  const cards = strategies.map((s) => {
    const current = s.id === "current";
    const title = current ? "Your current rotation" : s.name || "Rotation option";
    // API sentences in plain words (plainEvidence drops codes like I-01); confidence and sources as a small line.
    const item = (x) => {
      const e = plainEvidence(x);
      const meta = [e.confidence ? `Confidence: ${e.confidence}` : "", e.sources.length ? `Sources: ${e.sources.join(", ")}` : ""].filter(Boolean).join(" · ");
      return `<li>${esc(e.text)}${meta ? `<br><span class="small">${esc(meta)}</span>` : ""}</li>`;
    };
    const list = (items, empty) => (Array.isArray(items) && items.length ? `<ul>${items.map(item).join("")}</ul>` : `<p class="muted">${esc(empty)}</p>`);
    return `<article class="card${s.id === bestId ? " is-best" : ""}" aria-labelledby="c-${esc(s.id)}">
      ${s.id === bestId ? bestTag : ""}<h3 id="c-${esc(s.id)}" tabindex="-1">${esc(title)}</h3>
      <p class="small muted" style="margin-top:4px">${current ? "What you grow today. The other options are compared with it." : "An idea to talk over with your adviser. You decide."}</p>
      ${strip(s.years || [], `Crop sequence: ${title}`)}
      ${s.cover_crop ? `<p class="cover-note">${withIcon("leaf", `Plus a cover crop, <strong>${esc(cropName(s.cover_crop.crop, state.names))}</strong>, after year ${fmt(s.cover_crop.after_year)}.`)}</p>` : ""}
      <p class="gap-top">${esc(plainEvidence(s.why || "").text)}</p>
      <div class="gap-top">${meter(s.scores?.overall, s.labels?.overall)}</div>
      <h4>${withIcon("warning", "Check on your farm before deciding")}</h4>${list(s.risks_to_review, "No specific risks found. Still check with a local adviser.")}
      <details class="more"><summary>More detail</summary>
        <dl class="scores">${SCORE_ROWS.map(([k, name, l]) => `<div><dt>${withIcon(name, esc(l))}</dt><dd>${meter(s.scores?.[k], s.labels?.[k])}</dd></div>`).join("")}</dl>
        <h4>Why we suggest it</h4>${list(s.evidence, "No evidence listed.")}
        <h4>Benefits</h4>${list(s.benefits, current ? "This is the baseline, so no benefits are compared." : "No extra benefits found.")}
        <h4>What we don't know yet</h4>${list(s.gaps, "No information gaps listed.")}
      </details>
    </article>`;
  }).join("");

  const facts = keyFacts(profile);
  const trends = trendFacts(profile.trends);
  const loc = profile.location || {};
  const limits = [...(profile.limits?.en || [])];
  if (noNdvi) limits.unshift(loadingNdvi
    ? "Satellite photos (MODIS) were still loading for this point, so we can't tell the bare months yet."
    : "No satellite photos (MODIS) for this point, so we can't tell the bare months.");

  const head = `
  <div class="results-head">
    <a class="btn btn--secondary" href="#/" id="back">${withIcon("back", "Change answers")}</a>
    <h1 tabindex="-1" id="r-title">Results for ${esc(label)}</h1>
    <p class="small muted">Based on 21 years of NASA data (2005–2025). Not a forecast. Checked ${esc(formatDate(at))}.</p>
  </div>
  ${state.result.saved ? savedBanner(at) : ""}
  ${loadingNdvi
    ? banner("warn", "Satellite photos are still loading.", " Rain, heat and frost are ready. Bare months appear in 1–2 minutes. Keep this page open.")
    : noNdvi ? banner("warn", "No satellite photos for this point.", " We can't tell when the field is bare. Rain, heat and frost still work.") : ""}
  <div class="tabs" role="tablist" aria-label="Results">${TABS.map(([id, text]) => `
    <button type="button" class="tab" role="tab" id="tab-${id}" data-tab="${id}" aria-controls="panel" aria-selected="${id === tab}" tabindex="${id === tab ? 0 : -1}">${text}</button>`).join("")}
  </div>`;

  if (tab === "expect") {
    app.innerHTML = `${head}<div id="panel" role="tabpanel" aria-labelledby="tab-expect" tabindex="-1"></div>`;
    bindTabs();
    loadExpect();
    return;
  }

  app.innerHTML = `${head}
  <div id="panel" role="tabpanel" aria-labelledby="tab-results" tabindex="-1">
  ${answer}
  <section class="section" aria-labelledby="h-opt">
    <h2 id="h-opt">All options side by side</h2>
    <p class="small">Your current rotation first, then the others by score. Scores are out of 100. Good: 67 or more. Fair: 34–66. Poor: under 34. What matters to you counts more. Your answers: ${esc(weights)}.</p>
    <div class="gap-top">${compare}</div>
    ${limitsDetails("What the scores can't tell", [...SCORE_ROWS.map(([k, , l]) => [l, data?.score_limits?.[k]]), ["Overall", data?.score_limits?.overall]])}
    ${cards}
  </section>

  <section class="section" aria-labelledby="h-year">
    <h2 id="h-year">Your field through the year</h2>
    ${facts.length ? `<ul class="facts">${facts.map((f) => `<li><span class="ico" aria-hidden="true">${icon(f.icon)}</span><span>${esc(f.text)}</span></li>`).join("")}</ul>` : `<p class="muted">The climate summary for this field is not available. Try again later.</p>`}
    ${climateChart(profile)}
    ${calendar(profile, noNdvi)}
    ${limitsDetails("What these numbers can't tell", FIELD_LIMIT_ROWS.map(([k, l]) => [l, profile.field_limits?.[k]?.en]))}
  </section>

  <section class="section" aria-labelledby="h-trend">
    <h2 id="h-trend">Then and now</h2>
    <p class="small muted">${esc(profile.field_limits?.rain_change_pct?.en || "2016–2025 compared with 2005–2014 (10 years each). Not a forecast.")}</p>
    ${trends.length ? `<ul class="facts" style="margin-top:8px">${trends.map((f) => `<li><span class="ico" aria-hidden="true">${icon(f.icon)}</span><span>${esc(f.text)}</span></li>`).join("")}</ul>` : `<p class="muted">The comparison with earlier years is not available for this field.</p>`}
  </section>

  <section class="section foot" aria-labelledby="h-src">
    <h2 id="h-src">Where the data comes from</h2>
    <ul class="limits sources">${(profile.sources || []).map((s) => `<li>${esc(plainEvidence(s).text)}</li>`).join("") || "<li>NASA POWER</li>"}</ul>
    <p class="small muted" style="margin-top:8px">Field location used: ${fmtCoords(loc.lat, loc.lon)}${num(loc.elevation_m) !== null ? ` · ${fmt(loc.elevation_m, 0, "m")} above sea level` : ""}. Crop facts: FarmLens crop list. Sources are under each option.</p>
    <h3 style="margin-top:16px">Limits of these results</h3>
    <ul class="limits" style="margin-top:8px">${limits.map((l) => `<li>${esc(plainEvidence(l).text)}</li>`).join("")}</ul>
    <p style="margin-top:16px"><strong>${esc(data?.disclaimer || "This tool supports, and does not replace, your judgment and local agricultural advice.")}</strong></p>
    <div class="actions"><a class="btn btn--secondary" href="#/">${withIcon("back", "Change answers")}</a></div>
  </section>
  </div>`;
  bindTabs();
  $("[data-goto]")?.addEventListener("click", (e) => {
    const card = document.getElementById(e.currentTarget.dataset.goto);
    card.scrollIntoView({ block: "start" });
    card.focus({ preventScroll: true });
  });
}

/** Shown when an answer came from the phone's cache because there is no connection (sw.js). */
function savedBanner(iso) {
  const when = formatDate(iso);
  return banner("ok", `Saved result from ${when || "an earlier visit"} — you're offline`,
    " FarmLens saved this answer on this phone last time. Connect to the internet to refresh it.");
}

// ------------------------------------------------------------------ tabs & "What to expect"

/** Tabs follow the ARIA tabs pattern: arrows / Home / End move between them, the hash keeps Back working. */
function bindTabs() {
  const tabs = [...app.querySelectorAll('[role="tab"]')];
  tabs.forEach((btn, i) => {
    btn.addEventListener("click", () => openTab(btn.dataset.tab));
    btn.addEventListener("keydown", (e) => {
      const to = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: tabs.length - 1 }[e.key];
      if (to === undefined) return;
      e.preventDefault();
      openTab(tabs[(to + tabs.length) % tabs.length].dataset.tab);
    });
  });
}

function openTab(tab) {
  const hash = `#/${tab}`;
  if (location.hash !== hash) location.hash = hash; // route() renders and focuses the tab
}

function predictionsKey(inputs) {
  return api.predictionsQuery(inputs);
}

async function loadExpect() {
  const panel = $("#panel");
  const result = state.result;
  const key = predictionsKey(result.inputs);
  const free = !result.inputs.field;
  const show = async (data) => {
    const view = await import("./expect.js");
    if (state.result !== result || location.hash !== "#/expect" || !$("#panel")) return;
    $("#panel").innerHTML = (state.predictions?.saved != null && !state.result.saved ? savedBanner(state.predictions.saved) : "") +
      view.renderExpect(data, result.data?.profile);
    mountWarnings(data, result);
  };
  if (state.predictions?.key === key) {
    try { await show(state.predictions.data); return; } catch { /* the view module failed to load: fall through */ }
  }
  panel.innerHTML = `<div class="progress" role="status"><ol class="stages"><li class="active"><span class="mark" aria-hidden="true"><span class="spin"></span></span>Loading what to expect from NASA history…</li></ol></div>`;
  try {
    const [{ data, saved }] = await Promise.all([api.getPredictions(result.inputs, { freePoint: free }), import("./expect.js")]);
    state.predictions = { key, data, saved };
    await show(data);
  } catch (err) {
    if (state.result !== result || location.hash !== "#/expect" || !$("#panel")) return;
    const msg = errorMessage(err.kind || "server", { freePoint: free });
    $("#panel").innerHTML = `<div style="margin-top:16px">${banner("error", msg.title, ` ${msg.text}`,
      `<div class="actions"><button type="button" class="btn btn--primary" id="retry-expect">Try again</button><button type="button" class="btn btn--block" id="to-options">See rotation options</button></div>`)}</div>`;
    $("#retry-expect").addEventListener("click", loadExpect);
    $("#to-options").addEventListener("click", () => openTab("results"));
  }
}

/** Heavy-rain warnings on this phone (#42): loaded only when the alert card is on screen. */
async function mountWarnings(data, result) {
  const slot = $("#warn-slot");
  if (!slot) return;
  try {
    const [warn, fmtw] = await Promise.all([import("./notify.js"), import("./notify-format.js")]);
    if (!slot.isConnected) return;
    const { lang, ...saved } = result.inputs; // the answers, so a tap on the warning can open this field again
    warn.mountWarn(slot, { key: fmtw.fieldKey(result.inputs), name: result.label, inputs: saved, alerts: data?.alerts });
  } catch { /* the module failed to load: the card stays as it is, without the control */ }
}

/** A tap on a warning opens #/warning/<field key>: analyse that field again (saved answer offline) -> What to expect. */
async function openWarning(key) {
  history.replaceState(null, "", "#/");
  let entry = null;
  try { entry = (await import("./notify.js")).watched(key); } catch { /* no warnings module: plain start */ }
  const saved = entry?.inputs;
  const known = (saved?.rotation || []).filter((id) => state.names[id]);
  if (!saved || !known.length || (!saved.field && (num(saved.lat) === null || num(saved.lon) === null))) { route(); return; }
  if (saved.field && state.fields.some((f) => f.slug === saved.field)) {
    state.field = saved.field;
  } else {
    state.field = "map";
    state.point = { lat: saved.lat, lon: saved.lon };
  }
  Object.assign(state, {
    rotation: known, irrigation: saved.irrigation || state.irrigation, slope: saved.slope || state.slope,
    priorities: { ...state.priorities, ...(saved.priorities || {}) }, edited: true,
  });
  lastScreen = "form";
  state.mapApi = null;
  renderForm();
  runAnalysis("#/expect");
}

function climateChart(profile) {
  const months = (profile.months || []).slice().sort((a, b) => a.month - b.month);
  if (months.length !== 12 || months.some((m) => num(m.rain_mm) === null || num(m.et0_mm) === null)) {
    return `<p class="muted" style="margin-top:16px">The rain chart is not available for this field.</p>`;
  }
  const W = 340, H = 210, L = 34, B = 26, T = 10, R = 6;
  const top = Math.max(50, Math.ceil(Math.max(...months.flatMap((m) => [m.rain_mm, m.et0_mm])) / 50) * 50);
  const cw = (W - L - R) / 12;
  const y = (v) => T + (H - T - B) * (1 - v / top);
  const grid = [0, top / 2, top].map((v) => `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" stroke="currentColor" stroke-opacity="0.15"/><text x="${L - 4}" y="${y(v) + 5}" text-anchor="end">${v}</text>`).join("");
  const bars = months.map((m, i) => `<rect x="${L + i * cw + cw * 0.18}" y="${y(m.rain_mm)}" width="${cw * 0.64}" height="${y(0) - y(m.rain_mm)}" fill="var(--rain)"/>`).join("");
  const pts = months.map((m, i) => [L + i * cw + cw / 2, y(m.et0_mm)]);
  const line = `<polyline points="${pts.map((p) => p.join(",")).join(" ")}" fill="none" stroke="var(--need)" stroke-width="2.5" stroke-dasharray="6 4"/>` +
    pts.map(([px, py]) => `<path d="M${px} ${py - 5}l5 5-5 5-5-5z" fill="var(--need)"/>`).join("");
  const labels = months.map((m, i) => `<text x="${L + i * cw + cw / 2}" y="${H - 6}" text-anchor="middle">${MONTH_ABBR[m.month - 1][0]}</text>`).join("");
  const summary = months.map((m) => `${MONTHS[m.month - 1]}: rain ${fmt(m.rain_mm, 0)} mm, water lost ${fmt(m.et0_mm, 0)} mm`).join("; ");
  return `<h3 style="margin-top:24px">Rain and water a grass field loses (mm per month)</h3>
    <svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(summary)}">${grid}${bars}${line}${labels}</svg>
    <div class="legend"><span class="with-icon"><span style="color:var(--rain)">${icon("legend-bar")}</span><span>Bars: rain</span></span><span class="with-icon"><span style="color:var(--need)">${icon("legend-line")}</span><span>Dashed line: water lost by a short grass field (mm). Real crops differ.</span></span></div>
    <p class="small muted" style="margin-top:4px">Where the line is above the bars, rain alone does not cover it. Average month, 2005–2025.</p>`;
}

function calendar(profile, noNdvi) {
  const months = (profile.months || []).slice().sort((a, b) => a.month - b.month);
  if (!months.length) return "";
  // Each line: icon in its own column, so wrapped text lines up under the text, not under the icon.
  const line = (name, text) => `<span><i aria-hidden="true">${icon(name)}</i>${text}</span>`;
  // Field cover in three words (docs/indicators.md I-09): Bare below 0.25 (engine's likely_bare), Little cover
  // 0.25–0.35 (stubble, weeds, young crop), Green from 0.35. 0.35 is a display-only team assumption.
  const field = (m) => {
    if (m.likely_bare === true) return line("bare", "Bare");
    if (m.likely_bare !== false || num(m.ndvi) === null) return line("unknown", "Unknown");
    return num(m.ndvi) < LITTLE_COVER_NDVI ? line("stubble", "Little cover") : line("leaf", "Green");
  };
  // Non-breaking space keeps a number with its unit when the cell wraps.
  const days = (v, word) => `${fmt(v, 0)}&nbsp;${word}${Math.round(v) === 1 ? "" : "s"}`;
  const cells = months.map((m) => `<div><b>${MONTH_ABBR[m.month - 1]}</b>${line("rain", `${fmt(m.rain_mm, 0)}&nbsp;mm`)}${field(m)}${
    num(m.frost_days) >= 0.5 ? line("frost", days(m.frost_days, "frost day")) : ""}${num(m.heat_days) >= 0.5 ? line("sun", days(m.heat_days, "hot day")) : ""}</div>`).join("");
  const rows = months.map((m) => `<tr><td>${MONTH_ABBR[m.month - 1]}</td><td>${fmt(m.rain_mm, 0)}</td><td>${fmt(m.et0_mm, 0)}</td><td>${fmt(m.water_balance_mm, 0)}</td><td>${fmt(m.soil_wetness, 2)}</td><td>${fmt(m.frost_days, 1)}</td><td>${fmt(m.heat_days, 1)}</td><td>${fmt(m.heavy_rain_days, 1)}</td><td>${noNdvi ? "—" : fmt(m.ndvi, 2)}</td></tr>`).join("");
  return `<h3 style="margin-top:24px">Month by month</h3>
    <p class="small muted">Rain, field cover, and frost or very hot days (over 35 °C) per month. Field cover comes from satellite photos (2024–2025). "Little cover" means stubble or a young crop.</p>
    <div class="cal">${cells}</div>
    <details><summary>All numbers, month by month</summary>
      <div class="table-wrap" tabindex="0" role="region" aria-label="Monthly climate table"><table>
        <thead><tr><th>Month</th><th>Rain (mm)</th><th>Water lost (mm)</th><th>Balance (mm)</th><th>Soil moisture (0 dry–1 wet)</th><th>Frost days</th><th>Hot days (over 35 °C)</th><th>Very heavy rain days (30 mm+)</th><th>Plant cover (0 bare–1 green)</th></tr></thead>
        <tbody>${rows}</tbody></table></div>
      <p class="small muted" style="margin-top:8px">"Water lost" is what a short grass field loses to sun and wind. Real crops differ. Soil moisture is a model estimate.</p>
    </details>`;
}

// ------------------------------------------------------------------ router & connectivity

let lastScreen = null;

function route() {
  if (!state.crops.length) return;
  if (location.hash.startsWith("#/warning/")) {
    openWarning(decodeHashKey(location.hash));
    return;
  }
  const tab = { "#/results": "results", "#/expect": "expect" }[location.hash];
  if (tab && state.result) {
    state.mapApi = null;
    const fromTab = lastScreen === "results" || lastScreen === "expect";
    renderResults(tab);
    lastScreen = tab;
    if (fromTab) {
      $(`#tab-${tab}`).focus({ preventScroll: true }); // switching tabs: keep the place, focus stays on the tab
    } else {
      window.scrollTo(0, 0);
      $("#r-title").focus({ preventScroll: true });
    }
  } else {
    const n = Number(/^#\/step\/([1-4])$/.exec(location.hash)?.[1] || 1);
    if (lastScreen === "form" && $("#form")) { showStep(n); return; } // Next / Back / phone Back: same form
    lastScreen = "form";
    if (tab) history.replaceState(null, "", "#/");
    state.step = tab ? 1 : n;
    state.mapApi = null;
    renderForm();
    if (state.step > 1) $(`#s${state.step}`).focus({ preventScroll: true });
  }
}

function decodeHashKey(hash) {
  try { return decodeURIComponent(hash.slice("#/warning/".length)); } catch { return ""; }
}

function updateNet() { document.getElementById("net").hidden = navigator.onLine !== false; }

window.addEventListener("hashchange", route);
window.addEventListener("online", updateNet);
window.addEventListener("offline", updateNet);
updateNet();

if ("serviceWorker" in navigator) {
  // A new version takes over at once (skipWaiting in sw.js). Modules already loaded are the old ones, so ask
  // for a reload instead of mixing versions; the first install (no previous controller) needs nothing.
  const hadController = Boolean(navigator.serviceWorker.controller);
  navigator.serviceWorker.addEventListener("controllerchange", () => {
    if (!hadController || document.getElementById("update")) return;
    const box = document.createElement("div");
    box.id = "update";
    box.innerHTML = banner("ok", "FarmLens was updated", " Reload to use the new version.",
      `<div class="actions"><button type="button" class="btn btn--primary" id="reload">Reload now</button></div>`);
    document.querySelector(".page").prepend(box);
    box.querySelector("#reload").addEventListener("click", () => location.reload());
  });
  window.addEventListener("load", () => navigator.serviceWorker.register("sw.js").catch(() => {}));
  // A tap on a warning while FarmLens is already open: the service worker focuses this window and sends the link.
  navigator.serviceWorker.addEventListener("message", (e) => {
    const hash = e.data?.type === "farmlens-open" ? String(e.data.hash || "") : "";
    if (!hash.startsWith("#/warning/")) return;
    if (location.hash === hash) route();
    else location.hash = hash;
  });
}

// Warnings on this phone (#42): only when some are on, the small module is loaded to show the ones that are due.
try {
  if (localStorage.getItem("farmlens-warnings-v1")) {
    window.addEventListener("load", () => import("./notify.js").then((m) => m.checkWarnings()).catch(() => {}));
  }
} catch { /* storage blocked: no warnings */ }

boot();
