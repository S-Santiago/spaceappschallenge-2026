// "What to expect" tab (issue #40). Loaded on demand with import() the first time the tab opens, so it does not
// weigh on the first load. Returns HTML strings only (no DOM access), so node --test can render it with fixtures.
// Data: GET /api/predictions (P-01, P-02, P-03, P-07) + the Shape 1 profile already loaded (heat, I-06/I-11).

import { MONTHS, MONTH_ABBR, esc, fmt, limitsDetails, num, trendFacts } from "./format.js";
import {
  FROST_CAVEAT, basisFor, count, WEEKS, alertCards, frostSentences, fromMonth, heatFacts, heavySentence, mmdd, nextWeeks,
  rainYearSummary, returnSentence, weekOfYear,
} from "./expect-format.js";

// The "not a weather forecast" basis is said once, at the top of the tab, and repeated in the footer (UX review #40):
// repeating it in every card buried the content.
function card(title, body, extra = "") {
  return `<article class="card exp-card${extra}"><h4>${title}</h4>${body}</article>`;
}

/** 52-week strip of P-01 prob_rain, hand-drawn SVG (no chart library), with today marked. */
export function rainStrip(rainWeeks, today = new Date()) {
  const weeks = (rainWeeks || []).filter((w) => num(w?.prob_rain) !== null && num(w?.week) !== null)
    .sort((a, b) => a.week - b.week);
  if (weeks.length !== WEEKS) return "";
  const W = 340, H = 132, L = 40, R = 4, T = 18, B = 22;
  const bw = (W - L - R) / WEEKS;
  const y = (p) => T + (H - T - B) * (1 - p);
  const now = weekOfYear(today);
  const grid = [[0, "none"], [0.5, "half"], [1, "all"]].map(([p, label]) =>
    `<line x1="${L}" x2="${W - R}" y1="${y(p)}" y2="${y(p)}" stroke="currentColor" stroke-opacity="0.15"/>` +
    `<text x="${L - 4}" y="${y(p) + 4}" text-anchor="end">${label}</text>`).join("");
  const bars = weeks.map((w, i) => `<rect x="${(L + i * bw + 0.6).toFixed(1)}" y="${y(w.prob_rain).toFixed(1)}" width="${(bw - 1.2).toFixed(1)}" height="${(y(0) - y(w.prob_rain)).toFixed(1)}" fill="var(--rain)"${w.week === now ? "" : ' fill-opacity="0.75"'}/>`).join("");
  const seen = new Set();
  const labels = weeks.map((w, i) => {
    const m = Number(String(w.start).slice(0, 2));
    if (!m || seen.has(m)) return "";
    seen.add(m);
    return `<text x="${(L + i * bw + bw / 2).toFixed(1)}" y="${H - 6}" text-anchor="start">${MONTH_ABBR[m - 1][0]}</text>`;
  }).join("");
  const tx = L + (now - 1) * bw + bw / 2;
  const marker = `<line x1="${tx.toFixed(1)}" x2="${tx.toFixed(1)}" y1="${T - 2}" y2="${y(0)}" stroke="var(--ink)" stroke-width="2" stroke-dasharray="3 2"/>` +
    `<text x="${tx.toFixed(1)}" y="${T - 6}" text-anchor="${now > 44 ? "end" : now < 8 ? "start" : "middle"}" class="today">▼ Today</text>`;
  const summary = rainYearSummary(weeks);
  const label = `Chance of rain in each week of the year, from January to December. Today is in the week of ${mmdd(weeks[now - 1].start, true)}. ${summary || ""}`;
  return `<svg class="chart strip-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(label)}">${grid}${bars}${labels}${marker}</svg>
    <p class="small muted">Each bar is one week: how many of the last ${fmt(weeks[0].years, 0)} years had at least 1 mm of rain that week (none · half · all).</p>
    ${summary ? `<p style="margin-top:8px">${esc(summary)}</p>` : ""}
    <details><summary>All 52 weeks</summary>
      <div class="table-wrap" tabindex="0" role="region" aria-label="Rain week by week"><table>
        <thead><tr><th>Week of</th><th>Years with rain</th><th>More than 10 mm</th><th>Average mm</th></tr></thead>
        <tbody>${weeks.map((w) => `<tr${w.week === now ? ' class="now"' : ""}><td>${esc(mmdd(w.start) || "—")}${w.week === now ? " (today)" : ""}</td><td>${fmt(Math.round(w.prob_rain * w.years))} of ${fmt(w.years)}</td><td>${num(w.prob_useful_rain) === null ? "—" : `${Math.round(w.prob_useful_rain * w.years)} of ${w.years}`}</td><td>${fmt(w.mean_rain_mm, 1)}</td></tr>`).join("")}</tbody>
      </table></div></details>`;
}

function rainSection(pred, today) {
  const weeks = nextWeeks(pred?.rain_weeks, today);
  const rows = weeks.map((w, i) => {
    const wet = count(w?.prob_rain, w?.years), useful = count(w?.prob_useful_rain, w?.years);
    if (wet === null || !mmdd(w.start)) return "";
    const label = i === 0 ? `This week (from ${mmdd(w.start)})` : `Week of ${mmdd(w.start)}`;
    const rain = wet === 0 ? `no rain in the last ${w.years} years`
      : `rain in ${wet} of ${w.years} years${useful ? `, ${useful} with more than 10 mm` : ""}`;
    return `<li><span class="ico" aria-hidden="true">🌧️</span><span><strong>${esc(label)}</strong>: ${esc(rain)}</span></li>`;
  }).join("");
  const cards = rows ? card("🌧️ Rain week by week", `<ul class="facts">${rows}</ul>`) : "";
  const strip = rainStrip(pred?.rain_weeks, today);
  if (!cards && !strip) return "";
  return `<section class="section" aria-labelledby="h-rain"><h3 id="h-rain">Rain in the next 4 weeks</h3>
    ${cards || `<p class="muted">Week-by-week rain is not available for this field.</p>`}
    ${strip ? `<h4 class="sub">Rain through the year</h4>${strip}` : ""}</section>`;
}

function frostSection(pred) {
  const f = frostSentences(pred?.frost);
  if (!f.spring && !f.autumn) return "";
  const body = [
    f.spring ? `<p><strong>${f.none ? "Frost" : "Spring"}:</strong> ${esc(f.spring)}</p>` : "",
    f.autumn ? `<p style="margin-top:8px"><strong>Autumn:</strong> ${esc(f.autumn)}</p>` : "",
    f.safe ? `<p style="margin-top:8px">${esc(f.safe)}</p>` : "",
    `<p class="caveat">⚠️ ${esc(FROST_CAVEAT)}</p>`,
  ].join("");
  return `<section class="section" aria-labelledby="h-frost"><h3 id="h-frost">Frost</h3>${card("❄️ Last and first frost", body)}</section>`;
}

function heatSection(profile) {
  const heat = heatFacts(profile);
  if (!heat) return "";
  const trend = trendFacts({ heat_days_change: profile?.trends?.heat_days_change, baseline: profile?.trends?.baseline })[0];
  const body = `<p>${esc(heat.summary)}</p>
    ${heat.perMonth.length ? `<ul class="plain">${heat.perMonth.map((t) => `<li>${esc(t)}</li>`).join("")}</ul>` : ""}
    ${trend ? `<p style="margin-top:8px"><span aria-hidden="true">${trend.icon}</span> ${esc(trend.text)} <span class="small muted">(2016–2025 compared with 2005–2014: a change, not a proven trend)</span></p>` : ""}`;
  return `<section class="section" aria-labelledby="h-heat"><h3 id="h-heat">Heat</h3>${card("🔥 Very hot days", body)}</section>`;
}

function heavySection(pred, today) {
  const heavy = pred?.heavy_rain;
  if (!heavy || !Array.isArray(heavy.months)) return "";
  const th = num(heavy.threshold_mm) ?? 20;
  const m = today.getMonth() + 1;
  const upcoming = fromMonth(heavy.months, m).slice(0, 2).map((r) => heavySentence(r, th)).filter(Boolean);
  const peak = heavy.months.filter((r) => num(r.prob) !== null).reduce((a, b) => (b.prob > a.prob ? b : a), { prob: -1 });
  const peakText = peak.month && !fromMonth(heavy.months, m).slice(0, 2).includes(peak) ? heavySentence(peak, th) : null;
  const ret = returnSentence(heavy, 5);
  const lines = [...upcoming.map((t) => esc(t)), peakText ? `<strong>Stormiest month.</strong> ${esc(peakText)}` : null, ret ? esc(ret) : null]
    .filter(Boolean);
  if (!lines.length) return "";
  return `<section class="section" aria-labelledby="h-heavy"><h3 id="h-heavy">Heavy rain</h3>
    ${card("⛈️ Days with heavy rain", lines.map((t, i) => `<p${i ? ' style="margin-top:8px"' : ""}>${t}</p>`).join("") +
      `<p class="small muted" style="margin-top:8px">Rain averaged over about 50 km: a storm on your field can be stronger.</p>`)}</section>`;
}

/** P-07 alert cards — only when the payload has them; otherwise nothing at all (no placeholder). */
export function alertsSection(pred, today = new Date()) {
  const cards = alertCards(pred?.alerts, num(pred?.heavy_rain?.threshold_mm) ?? 20, today);
  if (!cards.length) return "";
  const level = cards.some((c) => c.level === "high") ? "high" : "medium";
  const sources = [...new Set(cards.flatMap((c) => (c.source ? c.source.split(" and ") : [])))].join(" and ");
  const rows = cards.map((c) => {
    const freq = /\((\d+ of \d+ years)\)/.exec(c.text)?.[1];
    return `<li><span class="ico" aria-hidden="true">${c.icon}</span><span><strong>${esc(MONTHS[c.month - 1])}</strong> <span class="level">${esc(c.levelWord)}</span>${
      freq ? ` heavy rain in ${esc(freq)}` : ""}</span></li>`;
  }).join("");
  return `<section class="section" aria-labelledby="h-alerts"><h3 id="h-alerts">Heavy rain on bare soil</h3>
    <article class="card exp-card alert alert--${level}" aria-label="Heavy rain on bare soil: ${cards.length} ${cards.length === 1 ? "month" : "months"}, upcoming first">
      <p>Heavy-rain days often fall when the field is bare in these months. Bare soil can wash away — a cover crop or leaving stubble helps.</p>
      <ul class="facts" style="margin-top:12px">${rows}</ul>
      <p class="small muted" style="margin-top:12px">${sources ? `Bare months from the ${esc(sources)}. ` : ""}${esc(cards[0].threshold)} Upcoming months first.</p>
    </article></section>`;
}

/** The whole tab panel. */
export function renderExpect(pred, profile, today = new Date()) {
  const sections = [alertsSection(pred, today), rainSection(pred, today), frostSection(pred), heatSection(profile), heavySection(pred, today)]
    .filter(Boolean).join("");
  const period = String(pred?.period || "2005-2025").replace("-", "–");
  return `<p class="basis basis--lead">ℹ️ ${esc(basisFor(pred?.period))}</p>
    ${sections || `<p class="muted" style="margin-top:16px">What to expect is not available for this field. Try again later, or try a demo field.</p>`}
    <section class="section foot" aria-labelledby="h-exp-src"><h3 id="h-exp-src">Where these numbers come from</h3>
      <p class="small" style="margin-top:8px">Counts of years in NASA POWER daily data, ${esc(period)}, for an area of about 50 km around your field. They say what happened in past years, not what the weather will do. Your valley, slope or coast can differ.</p>
      ${limitsDetails("What each prediction can't tell", [["Rain week by week", pred?.limits?.rain_weeks?.en], ["Frost", pred?.limits?.frost?.en],
        ["Heavy rain", pred?.limits?.heavy_rain?.en], ["Heavy rain on bare soil", pred?.limits?.alerts?.en]])}</section>`;
}
