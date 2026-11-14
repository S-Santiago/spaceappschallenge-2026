// "Point on the map": Leaflet (vendored, BSD-2-Clause) is loaded only when the farmer picks this option,
// so the demo-field path stays light. Tiles: OpenStreetMap (attribution shown in the map corner).

const MALAGA = [36.85, -4.6];
// Rough box around Málaga province: FarmLens crops and thresholds are set for this area.
const BOUNDS = { south: 36.3, north: 37.35, west: -5.65, east: -3.75 };

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

export function inMalaga({ lat, lon }) {
  return lat >= BOUNDS.south && lat <= BOUNDS.north && lon >= BOUNDS.west && lon <= BOUNDS.east;
}

/** Mount a map in `el`; calls onPick({lat, lon}) when the farmer taps it. Returns {setPoint}. */
export async function mountMap(el, start, onPick) {
  const L = await loadLeaflet();
  const map = L.map(el, { center: start ? [start.lat, start.lon] : MALAGA, zoom: start ? 12 : 9, tap: true });
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);
  let marker = null;
  const setPoint = (p, pan = false) => {
    const ll = [p.lat, p.lon];
    if (marker) marker.setLatLng(ll);
    else marker = L.circleMarker(ll, { radius: 11, color: "#FFFFFF", weight: 3, fillColor: "#A4432A", fillOpacity: 1 }).addTo(map);
    if (pan) map.setView(ll, Math.max(map.getZoom(), 12));
  };
  if (start) setPoint(start);
  map.on("click", (e) => {
    const p = { lat: Math.round(e.latlng.lat * 100) / 100, lon: Math.round(e.latlng.lng * 100) / 100 };
    setPoint(p);
    onPick(p);
  });
  return { setPoint };
}
