// Hand-drawn stroke icons (24x24, no library, no icon font). Every icon is decorative (aria-hidden): the word
// next to it carries the meaning, so an icon is never the only cue. Colour comes from currentColor.

const CLOUD = '<path d="M7 15h10a3.5 3.5 0 0 0 .4-7A5.5 5.5 0 0 0 6.8 9.2 3 3 0 0 0 7 15z"/>';
const SUN = '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>';
const BELL = '<path d="M6 16v-5a6 6 0 0 1 12 0v5l2 2H4z"/><path d="M10 21h4"/>';

const PATHS = {
  drop: '<path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z"/>',
  sprout: '<path d="M12 21v-9"/><path d="M12 12C12 8 9 6 5 6c0 4 3 6 7 6z"/><path d="M12 10c0-3 2.5-5 6-5 0 3.5-2.5 5-6 5z"/>',
  coins: '<ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6"/><path d="M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6"/>',
  shield: '<path d="M12 3l7 3v5c0 5-3 8.5-7 10-4-1.5-7-5-7-10V6z"/>',
  pin: '<path d="M12 21s-6-5.5-6-11a6 6 0 0 1 12 0c0 5.5-6 11-6 11z"/><circle cx="12" cy="10" r="2.5"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7"/>',
  back: '<path d="M19 12H5"/><path d="M11 6l-6 6 6 6"/>',
  next: '<path d="M5 12h14"/><path d="M13 6l6 6-6 6"/>',
  warning: '<path d="M12 3L2 20h20z"/><path d="M12 10v4"/><path d="M12 17h.01"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6"/><path d="M12 7.5h.01"/>',
  rain: `${CLOUD}<path d="M8 18l-1 3M12 18l-1 3M16 18l-1 3"/>`,
  storm: `${CLOUD}<path d="M13 15l-3 4h4l-2 3"/>`,
  frost: '<path d="M12 2v20M3.5 7l17 10M3.5 17l17-10"/><path d="M9 4l3 2 3-2M9 20l3-2 3 2"/>',
  sun: SUN,
  heat: SUN,
  leaf: '<path d="M5 19C5 11 10 5 20 5c0 10-6 15-14 15"/><path d="M5 19l8-8"/>',
  bare: '<path d="M2 19h20"/><path d="M5 15h3M11 15h3M17 15h2"/><path d="M7 11h2M14 11h3"/>',
  stubble: '<path d="M2 20h20"/><path d="M6 20v-5M10 20v-7M14 20v-5M18 20v-7"/>',
  unknown: '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.5v.7"/><path d="M12 17h.01"/>',
  "trend-up": '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
  "trend-down": '<path d="M3 7l6 6 4-4 8 8"/><path d="M15 17h6v-6"/>',
  "trend-flat": '<path d="M3 12h18"/><path d="M17 8l4 4-4 4"/>',
  bell: BELL,
  "bell-off": `${BELL}<path d="M3 3l18 18"/>`,
  today: '<path d="M6 8h12l-6 8z" fill="currentColor"/>',
  "legend-bar": '<rect x="5" y="5" width="14" height="14" rx="1" fill="currentColor"/>',
  "legend-line": '<path d="M2 12h4M10 12h4M18 12h4"/><path d="M12 8l4 4-4 4-4-4z" fill="currentColor"/>',
  more: '<circle cx="12" cy="5" r="1.5" fill="currentColor"/><circle cx="12" cy="12" r="1.5" fill="currentColor"/><circle cx="12" cy="19" r="1.5" fill="currentColor"/>',
  "chevron-right": '<path d="M9 6l6 6-6 6"/>',
};

export const ICON_NAMES = Object.keys(PATHS);

/** Inline SVG string for a named icon, or "" for an unknown name (never a broken box). */
export function icon(name) {
  const body = PATHS[name];
  if (!body) return "";
  return `<svg class="icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ` +
    `stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${body}</svg>`;
}

/** Icon + word. `html` must already be escaped by the caller. */
export function withIcon(name, html) {
  return `<span class="with-icon">${icon(name)}<span>${html}</span></span>`;
}
