// "Point on the map": Leaflet (vendored, BSD-2-Clause) is loaded only when the farmer picks this option,
// so the demo-field path stays light. Tiles: OpenStreetMap (attribution shown in the map corner).
// Only points inside Málaga province can be chosen: FarmLens crops and thresholds are set for this area.
// The province outline (malaga-area.js) decides it, for taps, the phone's location and place search alike.

import { searchPlaces } from "./api.js";
import { MALAGA_AREA } from "./malaga-area.js";

const MALAGA = [36.85, -4.6];
// Box around the province outline, used to keep the map on Málaga and to narrow place search.
const BOUNDS = { south: 36.29, north: 37.29, west: -5.62, east: -3.76 };
const PLACE_KINDS = new Set(["place", "boundary", "natural", "landuse"]); // Nominatim `category`

let loading = null;

function loadLeaflet() {
  if (window.L) return Promise.resolve(window.L);
  if (loading) return loading;
  loading = new Promise((resolve, reject) => {
    const css = document.createElement("link");
    css.rel = "stylesheet";
    css.href = "vendor/leaflet/leaflet.css";
    document.head.append(css);
    const js = document.createElement("script");
    js.src = "vendor/leaflet/leaflet.js";
    js.onload = () => resolve(window.L);
    js.onerror = () => { loading = null; reject(new Error("map")); };
    document.head.append(js);
  });
  return loading;
}

/** Ray casting: is [lat, lon] inside the ring? */
function inRing(lat, lon, ring) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [yi, xi] = ring[i];
    const [yj, xj] = ring[j];
    if ((yi > lat) !== (yj > lat) && lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

export function inMalaga({ lat, lon }) {
  if (lat < BOUNDS.south || lat > BOUNDS.north || lon < BOUNDS.west || lon > BOUNDS.east) return false;
  return MALAGA_AREA.some(([outer, ...holes]) => inRing(lat, lon, outer) && !holes.some((h) => inRing(lat, lon, h)));
}

export const roundPoint = (lat, lon) => ({ lat: Math.round(lat * 100) / 100, lon: Math.round(lon * 100) / 100 });

/**
 * Find a town or area by name with OpenStreetMap Nominatim (one request per search, never while typing,
 * as its usage policy asks). Only places in Málaga province count: the result must say province ES-MA and
 * its point must fall inside the outline. Resolves to {lat, lon, name} or null; rejects when offline.
 */
export async function findPlace(query) {
  const params = new URLSearchParams({
    q: query, format: "jsonv2", addressdetails: "1", limit: "8", countrycodes: "es", bounded: "1",
    viewbox: `${BOUNDS.west},${BOUNDS.north},${BOUNDS.east},${BOUNDS.south}`,
  });
  const hits = await searchPlaces(params);
  for (const h of hits) {
    // Places only (towns, villages, hamlets, farms, districts, valleys…), not streets or shops: a street
    // called "Sevilla" in Málaga must not answer a search for Sevilla.
    if (!PLACE_KINDS.has(h.category)) continue;
    const p = roundPoint(Number(h.lat), Number(h.lon));
    if (h.address?.["ISO3166-2-lvl6"] !== "ES-MA" || !inMalaga(p)) continue;
    const a = h.address;
    const town = a.city || a.town || a.village || a.municipality;
    const name = h.name || h.display_name.split(",")[0];
    return { ...p, name: town && town !== name ? `${name}, ${town}` : name };
  }
  return null;
}

/**
 * Mount a map in `el`; calls onPick({lat, lon}) when the farmer taps inside Málaga province.
 * A tap outside does not move the point: a short note on the map says why. Returns {setPoint}.
 */
export async function mountMap(el, start, onPick) {
  const L = await loadLeaflet();
  const area = L.latLngBounds([BOUNDS.south, BOUNDS.west], [BOUNDS.north, BOUNDS.east]);
  const map = L.map(el, {
    center: start ? [start.lat, start.lon] : MALAGA, zoom: start ? 12 : 8, minZoom: 8, tap: true,
    maxBounds: area.pad(0.15), maxBoundsViscosity: 1,
  });
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);
  // Grey out everything outside the province (a world-sized ring with Málaga cut out) and draw its border.
  const world = [[-89, -179], [-89, 179], [89, 179], [89, -179]];
  L.polygon([world, ...MALAGA_AREA.map((p) => p[0])], {
    stroke: false, fillColor: "#3B3B3B", fillOpacity: 0.35, interactive: false,
  }).addTo(map);
  L.polygon(MALAGA_AREA, { color: "#2E5B44", weight: 2, fill: false, interactive: false }).addTo(map);
  if (!start) map.fitBounds(area);

  let marker = null;
  const setPoint = (p, pan = false) => {
    const ll = [p.lat, p.lon];
    if (marker) marker.setLatLng(ll);
    else marker = L.circleMarker(ll, { radius: 11, color: "#FFFFFF", weight: 3, fillColor: "#A4432A", fillOpacity: 1 }).addTo(map);
    if (pan) map.setView(ll, Math.max(map.getZoom(), 12));
  };
  if (start) setPoint(start);
  map.on("click", (e) => {
    const p = roundPoint(e.latlng.lat, e.latlng.lng);
    if (!inMalaga(p)) {
      L.popup({ closeButton: false, autoPan: false, className: "map-note" })
        .setLatLng(e.latlng).setContent("Outside Málaga province. Tap inside the green border.").openOn(map);
      return;
    }
    map.closePopup();
    setPoint(p);
    onPick(p);
  });
  return { setPoint };
}
