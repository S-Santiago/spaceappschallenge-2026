// Only points in Málaga province can be chosen. Run: node --test tests/web
import assert from "node:assert/strict";
import { test } from "node:test";

import { findPlace, inMalaga, roundPoint } from "../../web/js/map.js";

test("inMalaga accepts towns in the province", () => {
  for (const [lat, lon] of [[37.02, -4.56], [36.74, -5.17], [36.72, -4.42], [36.76, -3.88], [37.05, -4.86]]) {
    assert.equal(inMalaga({ lat, lon }), true, `${lat}, ${lon}`);
  }
});

test("inMalaga rejects neighbouring provinces and the sea", () => {
  // Olvera (Cádiz), Loja (Granada), Osuna (Sevilla), Algeciras (Cádiz), Lucena (Córdoba), open sea
  for (const [lat, lon] of [[36.93, -5.27], [37.17, -4.15], [37.24, -5.1], [36.13, -5.45], [37.41, -4.48], [36.5, -4.5]]) {
    assert.equal(inMalaga({ lat, lon }), false, `${lat}, ${lon}`);
  }
});

test("roundPoint keeps two decimals", () => {
  assert.deepEqual(roundPoint(37.0234, -4.5678), { lat: 37.02, lon: -4.57 });
});

function fakeSearch(hits) {
  globalThis.fetch = async () => ({ ok: true, json: async () => hits, headers: { get: () => null } });
}
const hit = (name, category, lat, lon, prov = "ES-MA", extra = {}) =>
  ({ name, category, lat: String(lat), lon: String(lon), display_name: name, address: { "ISO3166-2-lvl6": prov, ...extra } });

test("findPlace returns the first place inside Málaga", async () => {
  fakeSearch([hit("Antequera", "boundary", 37.019, -4.561, "ES-MA", { town: "Antequera" })]);
  assert.deepEqual(await findPlace("Antequera"), { lat: 37.02, lon: -4.56, name: "Antequera" });
});

test("findPlace ignores streets and places outside the province", async () => {
  fakeSearch([
    hit("Calle Sevilla", "highway", 36.32, -5.25),
    hit("Olvera", "boundary", 36.93, -5.27, "ES-CA"),
  ]);
  assert.equal(await findPlace("Sevilla"), null);
});

test("findPlace names the municipality of a hamlet", async () => {
  fakeSearch([hit("Granada", "place", 36.41, -5.3, "ES-MA", { town: "Casares" })]);
  assert.equal((await findPlace("Granada")).name, "Granada, Casares");
});
