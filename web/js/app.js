// FarmLens PWA (decision 0005: vanilla JS, no build). Screens with a tiny hash router:
//   #/          the 4-step form (field → current rotation → priorities → farm)
//   #/results   tab "Rotation options": the answer from POST /api/analyze (real engine; no mock data anywhere)
//   #/expect    tab "What to expect": GET /api/predictions (statistics over NASA history), view loaded on demand

import * as api from "./api.js";
import {
  FIELD_LIMIT_ROWS, MONTH_ABBR, MONTHS, cropName, cropOption, errorMessage, esc, matchCrops, fmt, formatDate, keyFacts, levelText,
  limitsDetails, ndviMissing, num, trendFacts,
} from "./format.js";
import { inMalaga, mountMap } from "./map.js";

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
  ["water", "💧", "Save water"],
  ["soil", "🌱", "Soil health"],
  ["income", "💶", "Income"],
  ["risk", "🛡️", "Low climate risk"],
];
const PRIORITY_WORDS = ["Not important", "A little", "Important", "Very important"];
const IRRIGATION = [
  ["none", "No irrigation", "Rain only"],
  ["supplementary", "A little", "A few waterings in dry spells"],
  ["full", "Full", "Irrigated all season"],
];
const SLOPE = [
  ["flat", "Flat", "Water does not run off"],
  ["moderate", "Gentle slope", "Some runoff after heavy rain"],
  ["steep", "Steep", "Soil washes away after storms"],
];
const SCORE_ROWS = [
  ["water", "💧", "Water"],
  ["soil", "🌱", "Soil health"],
  ["income", "💶", "Income (illustrative)"],
  ["risk", "🛡️", "Climate safety"],
];
const FAMILY_LABEL = { cereal: "Cereal", legume: "Legume", oilseed: "Oilseed", forage: "Forage", cover: "Cover crop", fallow: "Fallow", other: "Other" };
const STAGES = ["Fetching NASA climate data…", "Checking field greenness…", "Comparing rotations…"];
const LITTLE_COVER_NDVI = 0.35; // calendar word "Little cover" between Bare (<0.25) and Green (docs/indicators.md I-09)

const state = {
  fields: [], crops: [], names: {}, types: {},
  field: null, point: null, mapApi: null,
  rotation: [], priorities: { water: 1, soil: 1, income: 1, risk: 1 }, irrigation: "none", slope: "flat",
  edited: false, busy: false, result: null,
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

function radioCards(name, options, current) {
  return `<div class="choices">${options.map(([value, title, hint]) => `
    <label class="choice"><input type="radio" name="${name}" value="${esc(value)}"${value === current ? " checked" : ""}>
      <span><strong>${esc(title)}</strong><span class="small muted">${esc(hint)}</span></span></label>`).join("")}</div>`;
}

function stepHead(n, title) {
  return `<div class="step-head"><span class="step-num" aria-hidden="true">${n}</span>
    <h2>${esc(title)}<span class="step-of">Step ${n} of 4</span></h2></div>`;
}

function banner(kind, title, text, actions = "") {
  return `<div class="banner banner--${kind}" role="${kind === "error" ? "alert" : "status"}"><strong>${esc(title)}</strong>${esc(text)}${actions}</div>`;
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
    app.innerHTML = masthead() + banner("error", "The crop list is empty", " FarmLens can't compare rotations without it. Try again in a minute.",
      `<div class="actions"><button class="btn btn--primary" id="retry-boot">Try again</button></div>`);
    $("#retry-boot").addEventListener("click", boot);
    return;
  }
  state.field = state.fields[0]?.slug || "map";
  applyPreset(state.field);
  route();
}

function masthead() {
  return `<header class="masthead">
    <div class="brand"><svg width="32" height="32" viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="14" fill="#2E5B44"/><path d="M14 46h36M14 38h36M14 30h36" stroke="#E3C26A" stroke-width="4" stroke-linecap="round"/><circle cx="44" cy="18" r="7" fill="#9CC27A"/></svg>
    <h1>FarmLens</h1></div>
    <p class="lead">Compare crop rotations for <strong>your field</strong> with NASA climate and satellite data. Answer 4 short steps, then tap <strong>Analyze my field</strong>.</p>
  </header>`;
}

// ------------------------------------------------------------------ form screen

function renderForm() {
  const fieldOptions = state.fields.map((f) => [f.slug, f.name, f.description]);
  fieldOptions.push(["map", "Another point on the map", "Tap your field on a map · Needs a connection"]);
  app.innerHTML = `${masthead()}
  <form id="form" novalidate>
    <section class="step" aria-labelledby="s1">
      ${stepHead(1, "Your field").replace("<h2>", '<h2 id="s1">')}
      <fieldset><legend>Where is your field?</legend>${radioCards("field", fieldOptions, state.field)}</fieldset>
      <div id="map-box" ${isFreePoint() ? "" : "hidden"}>
        <p class="small" style="margin-top:12px">Tap your field on the map, or use your phone's location.</p>
        <div class="map" id="map" aria-label="Map of Málaga province. Tap to choose your field."></div>
        <div class="actions"><button type="button" class="btn btn--block" id="locate">📍 Use my location</button></div>
      </div>
      <div class="location" id="where" aria-live="polite"></div>
    </section>

    <section class="step" aria-labelledby="s2">
      ${stepHead(2, "Your current rotation").replace("<h2>", '<h2 id="s2">')}
      <p class="small muted" id="preset-note"></p>
      <fieldset style="margin-top:12px"><legend>How many years before it repeats?</legend>
        <div class="segmented">${[1, 2, 3, 4].map((n) => `<label><input type="radio" name="years" value="${n}"${n === state.rotation.length ? " checked" : ""}><span>${n} ${n === 1 ? "year" : "years"}</span></label>`).join("")}</div>
      </fieldset>
      <datalist id="crop-list">${state.crops.map((c) => `<option value="${esc(cropOption(c))}"></option>`).join("")}</datalist>
      <div id="years" style="margin-top:16px">${yearRows()}</div>
      <div id="strip" style="margin-top:16px">${strip(state.rotation, "Your current rotation")}</div>
    </section>

    <section class="step" aria-labelledby="s3">
      ${stepHead(3, "Your priorities").replace("<h2>", '<h2 id="s3">')}
      <p class="small muted">How much does each one matter to you? 0 = not important, 3 = very important.</p>
      <div style="margin-top:12px">${PRIORITIES.map(([k, icon, label]) => `
        <fieldset class="prio"><div class="prio-head"><legend style="margin:0">${icon} ${esc(label)}</legend><span class="small muted" id="pw-${k}">${PRIORITY_WORDS[state.priorities[k]]}</span></div>
          <div class="segmented">${[0, 1, 2, 3].map((v) => `<label><input type="radio" name="p-${k}" value="${v}"${v === state.priorities[k] ? " checked" : ""} aria-label="${esc(label)}: ${v}, ${PRIORITY_WORDS[v]}"><span>${v}</span></label>`).join("")}</div>
        </fieldset>`).join("")}</div>
    </section>

    <section class="step" aria-labelledby="s4">
      ${stepHead(4, "Your farm").replace("<h2>", '<h2 id="s4">')}
      <fieldset><legend>Irrigation: how much water can you add besides rain?</legend>${radioCards("irrigation", IRRIGATION, state.irrigation)}</fieldset>
      <fieldset style="margin-top:16px"><legend>Slope of the field</legend>${radioCards("slope", SLOPE, state.slope)}</fieldset>
    </section>

    <div class="step">
      <button type="submit" class="btn btn--primary" id="go">Analyze my field</button>
      <div id="feedback" aria-live="polite"></div>
    </div>
  </form>`;

  updateWhere();
  const form = $("#form");
  form.addEventListener("change", onChange);
  form.addEventListener("input", onCropInput);
  form.addEventListener("focusin", onCropFocus);
  form.addEventListener("focusout", onCropBlur);
  form.addEventListener("submit", (e) => { e.preventDefault(); runAnalysis(); });
  $("#locate").addEventListener("click", locate);
  if (isFreePoint()) openMap();
}

function updateWhere() {
  const where = $("#where");
  const note = $("#preset-note");
  if (isFreePoint()) {
    if (!state.point) {
      where.innerHTML = `<span class="muted">No point chosen yet. Tap the map to choose your field.</span>`;
    } else {
      const outside = inMalaga(state.point) ? "" : `<br><span class="small">⚠️ This point is outside Málaga province. FarmLens crops and rules are set for Málaga, so results may not fit.</span>`;
      where.innerHTML = `📍 Your point: <strong>${fmt(state.point.lat, 2)}, ${fmt(state.point.lon, 2)}</strong>
        <br><span class="small muted">The first analysis of a new point fetches NASA data live and can take up to a minute.</span>${outside}`;
    }
    note.textContent = "Example rotation filled in. Change it to match your field.";
  } else {
    const f = fieldInfo();
    where.innerHTML = f ? `📍 <strong>${esc(f.name)}</strong> · ${fmt(f.lat, 2)}, ${fmt(f.lon, 2)} · ${fmt(f.elevation_m, 0, "m")} above sea level` : "";
    note.textContent = state.edited ? "" : "Example rotation for this area filled in. Change it to match your field.";
  }
}

// One text field per year with the crop names as suggestions (<datalist>): type part of a name, pick it.
function yearRows() {
  return state.rotation.map((id, i) => `
    <div class="year-row"><label for="y${i}">Year ${i + 1}</label>
      <input id="y${i}" class="crop-input" data-year="${i}" list="crop-list" value="${esc(cropName(id, state.names))}"
        autocomplete="off" autocapitalize="none" spellcheck="false" enterkeyhint="done"
        placeholder="Type a crop or Latin name, e.g. wheat" aria-describedby="y${i}-hint">
      <p class="field-hint" id="y${i}-hint" role="status"></p></div>`).join("");
}

function setYear(input, id) {
  state.rotation[Number(input.dataset.year)] = id;
  state.edited = true;
  $("#strip").innerHTML = strip(state.rotation, "Your current rotation");
  updateWhere();
}

/** While typing: as soon as the text names exactly one crop (e.g. picked from the suggestions), use it. */
function onCropInput(e) {
  const t = e.target;
  if (t.dataset.year === undefined) return;
  // A suggestion picked from the list arrives as its full text ("Sunflower · Helianthus annuus").
  const picked = state.crops.find((c) => cropOption(c) === t.value.trim() || c.name === t.value.trim());
  if (picked) setYear(t, picked.id);
}

/** On focus the field is emptied so every suggestion shows; leaving it resolves or restores the crop. */
function onCropFocus(e) {
  const t = e.target;
  if (t.dataset.year === undefined) return;
  t.placeholder = t.value || "Type a crop or Latin name, e.g. wheat";
  t.value = "";
  $(`#${t.id}-hint`).textContent = "";
  t.removeAttribute("aria-invalid");
}

function onCropBlur(e) {
  const t = e.target;
  if (t.dataset.year === undefined) return;
  const i = Number(t.dataset.year);
  const typed = t.value.trim();
  const hits = matchCrops(typed, state.crops);
  const kept = cropName(state.rotation[i], state.names);
  if (hits.length === 1) {
    setYear(t, hits[0].id);
  } else if (typed) {
    $(`#${t.id}-hint`).textContent = hits.length
      ? `"${typed}" matches ${hits.length} crops (${hits.slice(0, 4).map((c) => c.name).join(", ")}${hits.length > 4 ? "…" : ""}), so ${kept} was kept. Pick one of the suggestions.`
      : `"${typed}" is not in the crop list, so ${kept} was kept. Type part of a common or Latin name and pick one of the suggestions.`;
    t.setAttribute("aria-invalid", "true");
  }
  t.value = cropName(state.rotation[i], state.names);
  t.placeholder = "Type a crop or Latin name, e.g. wheat";
}

function renderYears() {
  $("#years").innerHTML = yearRows();
  $("#strip").innerHTML = strip(state.rotation, "Your current rotation");
  app.querySelectorAll('input[name="years"]').forEach((r) => { r.checked = Number(r.value) === state.rotation.length; });
}

function onChange(e) {
  const t = e.target;
  $("#feedback").innerHTML = "";
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
    // crop text fields are handled on input / focus / blur (onCropInput, onCropFocus, onCropBlur)
  } else if (t.name.startsWith("p-")) {
    const k = t.name.slice(2);
    state.priorities[k] = Number(t.value);
    $(`#pw-${k}`).textContent = PRIORITY_WORDS[state.priorities[k]];
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
      state.point = { lat: Math.round(pos.coords.latitude * 100) / 100, lon: Math.round(pos.coords.longitude * 100) / 100 };
      state.mapApi?.setPoint(state.point, true);
      updateWhere();
    },
    () => { where.innerHTML = `<span>We couldn't get your location. Allow location for this site, or tap the map instead.</span>`; },
    { enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 },
  );
}

// ------------------------------------------------------------------ analysis

async function runAnalysis() {
  if (state.busy) return;
  const feedback = $("#feedback");
  if (isFreePoint() && !state.point) {
    feedback.innerHTML = banner("error", "Choose your field first", " Tap the map in step 1, or pick a demo field.");
    $("#where").scrollIntoView({ block: "center" });
    return;
  }
  const free = isFreePoint();
  const go = $("#go");
  state.busy = true;
  go.disabled = true;
  go.textContent = "Analyzing…";
  feedback.innerHTML = `<div class="progress" role="status"><ol class="stages">${STAGES.map((s) => `<li><span class="mark" aria-hidden="true">·</span>${s}</li>`).join("")}</ol><p class="small muted" id="elapsed"></p></div>`;
  const items = [...feedback.querySelectorAll(".stages li")];
  const setStage = (i) => items.forEach((li, j) => {
    li.className = j < i ? "done" : j === i ? "active" : "";
    li.querySelector(".mark").innerHTML = j < i ? "✓" : j === i ? '<span class="spin"></span>' : "·";
  });
  // The API does the three stages in one request (POWER, then MODIS, then the rotation engine), so the list
  // follows the typical timing: POWER answers in ~2 s, MODIS is the slow one for a new point.
  setStage(0);
  const started = Date.now();
  const tick = setInterval(() => {
    const s = Math.round((Date.now() - started) / 1000);
    if (s >= 2) setStage(1);
    const el = $("#elapsed");
    if (el && s >= 5) el.textContent = `${s} s · ${free ? "New points take longer the first time. Next time it is instant." : "Still working…"}`;
  }, 500);

  const body = inputs();
  try {
    const { data, saved } = await api.analyze(body, { freePoint: free });
    setStage(2);
    state.result = { data, inputs: body, at: saved || new Date().toISOString(), saved: saved !== null, label: free ? `your point (${fmt(body.lat, 2)}, ${fmt(body.lon, 2)})` : fieldInfo()?.name || "your field" };
    watchPending(state.result);
    setStage(3);
    location.hash = "#/results";
  } catch (err) {
    const msg = errorMessage(err.kind || "server", { freePoint: free });
    feedback.innerHTML = banner("error", msg.title, ` ${msg.text}`,
      `<div class="actions"><button type="button" class="btn btn--primary" id="retry">Try again</button>${
        free && state.fields.length ? `<button type="button" class="btn btn--block" id="use-demo">Use a demo field</button>` : ""}</div>`);
    $("#retry").addEventListener("click", runAnalysis);
    $("#use-demo")?.addEventListener("click", () => {
      const first = app.querySelector(`input[name="field"][value="${state.fields[0].slug}"]`);
      first.checked = true;
      first.dispatchEvent(new Event("change", { bubbles: true }));
      first.focus();
      first.scrollIntoView({ block: "center" });
    });
  } finally {
    clearInterval(tick);
    state.busy = false;
    const btn = $("#go");
    if (btn) { btn.disabled = false; btn.textContent = "Analyze my field"; }
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

function scoreBar(value, label) {
  const n = Math.max(0, Math.min(100, num(value) ?? 0));
  return `<div class="bar bar--${levelKey(label, value)}" aria-hidden="true"><i style="width:${n}%"></i></div>`;
}

function renderResults(tab = "results") {
  const { data, label, at, inputs: used } = state.result;
  const profile = data?.profile || {};
  const strategies = Array.isArray(data?.strategies) ? data.strategies : [];
  const weights = PRIORITIES.map(([k, icon, l]) => `${icon} ${l} ${used.priorities[k]}`).join(" · ");
  const loadingNdvi = isPending(state.result);
  const noNdvi = ndviMissing(profile);

  // DESIGN.md "Tags": only the alternative with the highest overall score gets "Best fit for your priorities".
  const alternatives = strategies.filter((s) => s.id !== "current" && num(s.scores?.overall) !== null);
  const bestId = alternatives.length ? alternatives.reduce((a, b) => (num(b.scores.overall) > num(a.scores.overall) ? b : a)).id : null;
  const bestTag = `<span class="tag">Best fit for your priorities</span>`;

  const compare = strategies.length ? `<ul class="compare">${strategies.map((s) => `
      <li${s.id === bestId ? ' class="is-best"' : ""}>${s.id === bestId ? bestTag : ""}<div class="row"><span>${esc(s.id === "current" ? "Your current rotation" : s.name || "Rotation option")}</span><span class="score">${fmt(s.scores?.overall)}/100 · ${levelText(s.labels?.overall, s.scores?.overall)}</span></div>
        <div class="small muted">${esc((s.years || []).map((id) => cropName(id, state.names)).join(" → "))}${s.cover_crop ? ` + ${esc(cropName(s.cover_crop.crop, state.names))}` : ""}</div>
        ${scoreBar(s.scores?.overall, s.labels?.overall)}</li>`).join("")}</ul>`
    : banner("warn", "No rotation options could be built for this field", " Check your answers and try again, or try a demo field.");

  const cards = strategies.map((s) => {
    const current = s.id === "current";
    const title = current ? "Your current rotation" : s.name || "Rotation option";
    const list = (items, empty) => (Array.isArray(items) && items.length ? `<ul>${items.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : `<p class="muted">${esc(empty)}</p>`);
    return `<article class="card${s.id === bestId ? " is-best" : ""}" aria-labelledby="c-${esc(s.id)}">
      ${s.id === bestId ? bestTag : ""}<h3 id="c-${esc(s.id)}">${esc(title)}</h3>
      <p class="small muted" style="margin-top:4px">${current ? "What you grow today. The other options are compared with it." : "A suggestion to discuss with your adviser, not an order."}</p>
      ${strip(s.years || [], `Crop sequence: ${title}`)}
      ${s.cover_crop ? `<p class="cover-note">🌿 Plus a cover crop, <strong>${esc(cropName(s.cover_crop.crop, state.names))}</strong>, after year ${fmt(s.cover_crop.after_year)}.</p>` : ""}
      <p style="margin-top:12px">${esc(s.why || "")}</p>
      <dl class="scores">${SCORE_ROWS.map(([k, icon, l]) => `<div><dt>${icon} ${l}</dt><dd>${fmt(s.scores?.[k])}/100 · ${levelText(s.labels?.[k], s.scores?.[k])}</dd>${scoreBar(s.scores?.[k], s.labels?.[k])}</div>`).join("")}</dl>
      <h4>⚠️ Check locally before deciding</h4>${list(s.risks_to_review, "No specific risks found. Still check with a local adviser.")}
      <details><summary>Why we suggest it (evidence)</summary>${list(s.evidence, "No evidence listed.")}</details>
      <details><summary>Benefits</summary>${list(s.benefits, current ? "This is the baseline, so no benefits are compared." : "No extra benefits found.")}</details>
      <details><summary>What we don't know yet</summary>${list(s.gaps, "No information gaps listed.")}</details>
    </article>`;
  }).join("");

  const facts = keyFacts(profile);
  const trends = trendFacts(profile.trends);
  const loc = profile.location || {};
  const limits = [...(profile.limits?.en || [])];
  if (noNdvi) limits.unshift(loadingNdvi
    ? "Greenness data (MODIS) was still loading for this point, so the months when the field is bare are not known yet."
    : "Greenness data (MODIS) was not available for this point, so the months when the field is bare are unknown.");

  const head = `
  <div class="results-head">
    <a class="btn" href="#/" id="back">← Change answers</a>
    <h1 tabindex="-1" id="r-title">Results for ${esc(label)}</h1>
    <p class="small muted">Based on NASA data for 2005–2025 · analysed ${esc(formatDate(at))}</p>
  </div>
  ${state.result.saved ? savedBanner(at) : ""}
  ${loadingNdvi
    ? banner("warn", "Satellite greenness is still loading", " Rain, heat and frost results are ready. The months when the field is bare will be added here automatically in a minute or two. Keep this page open.")
    : noNdvi ? banner("warn", "Greenness data unavailable for this point", " Bare months are unknown. Rain, heat and frost still come from NASA POWER.") : ""}
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
  <section class="section" aria-labelledby="h-opt">
    <h2 id="h-opt">Rotation options</h2>
    <p class="small muted">Your current rotation first, then other options by overall score. Scores out of 100 (Good 67 or more · Fair 34–66 · Poor under 34), weighted by your priorities: ${esc(weights)}.</p>
    <div style="margin-top:12px">${compare}</div>
    ${limitsDetails("What the scores can't tell", [...SCORE_ROWS.map(([k, , l]) => [l, data?.score_limits?.[k]]), ["Overall", data?.score_limits?.overall]])}
    ${cards}
  </section>

  <section class="section" aria-labelledby="h-year">
    <h2 id="h-year">Your field through the year</h2>
    ${facts.length ? `<ul class="facts">${facts.map((f) => `<li><span class="ico" aria-hidden="true">${f.icon}</span><span>${esc(f.text)}</span></li>`).join("")}</ul>` : `<p class="muted">The climate summary for this field is not available. Try again later.</p>`}
    ${climateChart(profile)}
    ${calendar(profile, noNdvi)}
    ${limitsDetails("What these numbers can't tell", FIELD_LIMIT_ROWS.map(([k, l]) => [l, profile.field_limits?.[k]?.en]))}
  </section>

  <section class="section" aria-labelledby="h-trend">
    <h2 id="h-trend">Then and now</h2>
    <p class="small muted">${esc(profile.field_limits?.rain_change_pct?.en || "2016–2025 compared with 2005–2014.")}</p>
    ${trends.length ? `<ul class="facts" style="margin-top:8px">${trends.map((f) => `<li><span class="ico" aria-hidden="true">${f.icon}</span><span>${esc(f.text)}</span></li>`).join("")}</ul>` : `<p class="muted">The comparison with earlier years is not available for this field.</p>`}
  </section>

  <section class="section foot" aria-labelledby="h-src">
    <h2 id="h-src">Where the data comes from</h2>
    <ul class="limits sources">${(profile.sources || []).map((s) => `<li>${esc(s)}</li>`).join("") || "<li>NASA POWER</li>"}</ul>
    <p class="small muted" style="margin-top:8px">Field location used: ${fmt(loc.lat, 2)}, ${fmt(loc.lon, 2)}${num(loc.elevation_m) !== null ? ` · ${fmt(loc.elevation_m, 0, "m")}` : ""}. Crop traits: FarmLens crop catalogue (sources in each card's evidence).</p>
    <h3 style="margin-top:16px">Limits of these results</h3>
    <ul class="limits" style="margin-top:8px">${limits.map((l) => `<li>${esc(l)}</li>`).join("")}</ul>
    <p style="margin-top:16px"><strong>${esc(data?.disclaimer || "This tool supports, and does not replace, your judgment and local agricultural advice.")}</strong></p>
    <div class="actions"><a class="btn btn--block" href="#/">← Change answers</a></div>
  </section>
  </div>`;
  bindTabs();
}

/** Shown when an answer came from the phone's cache because there is no connection (sw.js). */
function savedBanner(iso) {
  const when = formatDate(iso);
  return banner("ok", `Saved result from ${when || "an earlier visit"} — you're offline`,
    " This is the answer FarmLens saved on this phone last time. Connect to the internet to refresh it.");
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
  const summary = months.map((m) => `${MONTHS[m.month - 1]}: rain ${fmt(m.rain_mm, 0)} mm, water need ${fmt(m.et0_mm, 0)} mm`).join("; ");
  return `<h3 style="margin-top:24px">Rain and water need (mm per month)</h3>
    <svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(summary)}">${grid}${bars}${line}${labels}</svg>
    <div class="legend"><span><span style="color:var(--rain)">■</span> Bars = rain</span><span><span style="color:var(--need)">◆ - -</span> Line = water the air takes from a crop (ET0)</span></div>
    <p class="small muted" style="margin-top:4px">Where the line is above the bars, the field is short of water. Average month, 2005–2025.</p>`;
}

function calendar(profile, noNdvi) {
  const months = (profile.months || []).slice().sort((a, b) => a.month - b.month);
  if (!months.length) return "";
  // Each line: pictogram in its own column, so wrapped text lines up under the text, not under the icon.
  const line = (icon, text) => `<span><i aria-hidden="true">${icon}</i>${text}</span>`;
  // Field cover in three words (docs/indicators.md I-09): Bare below 0.25 (engine's likely_bare), Little cover
  // 0.25–0.35 (stubble, weeds, young crop), Green from 0.35. 0.35 is a display-only team assumption.
  const field = (m) => {
    if (m.likely_bare === true) return line("🟫", "Bare");
    if (m.likely_bare !== false || num(m.ndvi) === null) return line("❔", "Unknown");
    return num(m.ndvi) < LITTLE_COVER_NDVI ? line("🌾", "Little cover") : line("🌿", "Green");
  };
  // Non-breaking space keeps a number with its unit when the cell wraps.
  const days = (v, word) => `${fmt(v, 0)}&nbsp;${word}${Math.round(v) === 1 ? "" : "s"}`;
  const cells = months.map((m) => `<div><b>${MONTH_ABBR[m.month - 1]}</b>${line("🌧️", `${fmt(m.rain_mm, 0)}&nbsp;mm`)}${field(m)}${
    num(m.frost_days) >= 0.5 ? line("❄️", days(m.frost_days, "frost day")) : ""}${num(m.heat_days) >= 0.5 ? line("🔥", days(m.heat_days, "hot day")) : ""}</div>`).join("");
  const rows = months.map((m) => `<tr><td>${MONTH_ABBR[m.month - 1]}</td><td>${fmt(m.rain_mm, 0)}</td><td>${fmt(m.et0_mm, 0)}</td><td>${fmt(m.water_balance_mm, 0)}</td><td>${fmt(m.soil_wetness, 2)}</td><td>${fmt(m.frost_days, 1)}</td><td>${fmt(m.heat_days, 1)}</td><td>${fmt(m.heavy_rain_days, 1)}</td><td>${noNdvi ? "—" : fmt(m.ndvi, 2)}</td></tr>`).join("");
  return `<h3 style="margin-top:24px">Month by month</h3>
    <p class="small muted">Rain, field cover (satellite greenness 2024–2025: bare, little cover such as stubble or a young crop, or green), and frost or very hot days (over 35 °C) per month.</p>
    <div class="cal">${cells}</div>
    <details><summary>All numbers, month by month</summary>
      <div class="table-wrap" tabindex="0" role="region" aria-label="Monthly climate table"><table>
        <thead><tr><th>Month</th><th>Rain mm</th><th>Need mm</th><th>Balance mm</th><th>Soil wet 0–1</th><th>Frost d</th><th>Hot d</th><th>Storm d (≥30 mm)</th><th>Green 0–1</th></tr></thead>
        <tbody>${rows}</tbody></table></div>
      <p class="small muted" style="margin-top:8px">"Need" is reference evapotranspiration (ET0, FAO-56). "Soil wet" is a model estimate. Definitions in docs/indicators.md.</p>
    </details>`;
}

// ------------------------------------------------------------------ router & connectivity

let lastScreen = null;

function route() {
  if (!state.crops.length) return;
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
    lastScreen = "form";
    if (tab) history.replaceState(null, "", "#/");
    state.mapApi = null;
    renderForm();
  }
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
}

boot();
