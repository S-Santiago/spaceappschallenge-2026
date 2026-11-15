// The "field story" loader (DESIGN.md "Loading"): a small hand-drawn inline SVG that tells what the one analysis
// request is doing — a satellite passes over (NASA data), its beam scans the field (satellite photos), then the
// crop plots grow (comparing rotations). The scene is decorative (aria-hidden); the stage list and one polite
// live region carry the meaning. CSS animates only transform and opacity, and reduced motion shows it still.
// Pure functions returning HTML strings, so node --test can check them.

import { icon } from "./icons.js";

/** The scene. `variant`: "story" (analysis, reacts to data-stage), "splash" (start-up screen; the same markup is
 * written statically in web/index.html so it paints before any JS, and a test keeps the two equal), "map", "expect". */
export function fieldScene(variant = "story") {
  const sky = variant === "map" ? "" : `
  <path class="orbit" d="M-10 40Q164-10 338 40"/>
  <g class="sat"><g transform="translate(164 18)">
    <path class="beam" d="M0 6L-22 92h44z"/>
    <rect x="-6" y="-6" width="12" height="12" rx="2"/><rect x="-22" y="-3" width="13" height="6"/><rect x="9" y="-3" width="13" height="6"/>
  </g></g>
  <g class="cloud" transform="translate(58 46)"><path d="M-12 6h22a7 7 0 0 0 1-14 11 11 0 0 0-21 2 6 6 0 0 0-2 12z"/><path d="M-6 12l-2 6M2 12l-2 6M10 12l-2 6"/></g>
  <g class="sun" transform="translate(268 46)"><circle r="9"/><path d="M0-16v4M0 12v4M-16 0h4M12 0h4M-11-11l3 3M8 8l3 3M-11 11l3-3M8-8l3-3"/></g>`;
  const plots = [["cereal", 24, 96], ["legume", 98, 94], ["cereal", 172, 92], ["legume", 246, 90]]
    .map(([f, x, y]) => `<rect class="plot plot--${f}" x="${x}" y="${y}" width="60" height="${120 - y}" rx="4"/>`).join("");
  return `<svg class="scene scene--${variant}" viewBox="0 0 328 136" aria-hidden="true" focusable="false">${sky}
  <path class="soil" d="M0 112L328 100V136H0z"/><g class="plots">${plots}</g></svg>`;
}

/** The analysis loader: scene + stage list + elapsed line + one live region (filled by setStage, not every frame). */
export function storyLoader(stages) {
  return `<div class="progress progress--story" data-stage="0">${fieldScene("story")}` +
    `<ol class="stages">${stages.map((s) => `<li><span class="mark" aria-hidden="true">${DOT}</span>${s}</li>`).join("")}</ol>` +
    `<p class="small" id="elapsed"></p><p class="sr-only" role="status" aria-live="polite" id="stage-live"></p></div>`;
}

/** A one-line loader with a lighter scene (app start, map, What to expect). */
export function quietLoader(text, variant) {
  return `<div class="progress progress--quiet" role="status">${fieldScene(variant)}<p>${text}</p></div>`;
}

const DOT = '<span class="dot"></span>';

/** Marks for each stage row at step `i` (0-based; `stages.length` = all done): "done" | "active" | "". */
export function stageStates(count, i) {
  return Array.from({ length: count }, (_, j) => (j < i ? "done" : j === i ? "active" : ""));
}

/** Mark HTML for one row state. */
export function stageMark(st) {
  return st === "done" ? icon("check") : st === "active" ? '<span class="spin"></span>' : DOT;
}
