// Unit tests for the field-story loader (web/js/scene.js). Run: node --test tests/web
import assert from "node:assert/strict";
import { test } from "node:test";

import { fieldScene, quietLoader, stageMark, stageStates, storyLoader } from "../../web/js/scene.js";

const STAGES = ["Getting NASA data…", "Checking satellite photos of your field…", "Comparing rotations…"];

test("stageStates marks earlier stages done, the current one active, never all done early", () => {
  assert.deepEqual(stageStates(3, 0), ["active", "", ""]);
  assert.deepEqual(stageStates(3, 1), ["done", "active", ""]);
  assert.deepEqual(stageStates(3, 2), ["done", "done", "active"]);
  assert.deepEqual(stageStates(3, 3), ["done", "done", "done"]);
});

test("stage marks: check icon when done, spinner when active, plain dot otherwise", () => {
  assert.match(stageMark("done"), /<svg/);
  assert.match(stageMark("active"), /class="spin"/);
  assert.match(stageMark(""), /class="dot"/);
});

test("the scene is decorative and every variant draws the field", () => {
  for (const v of ["story", "start", "map", "expect"]) {
    const svg = fieldScene(v);
    assert.match(svg, /aria-hidden="true"/);
    assert.equal((svg.match(/class="plot /g) || []).length, 4);
  }
  assert.doesNotMatch(fieldScene("map"), /class="sat"/);
});

test("the story loader has one polite live region and starts at stage 0 with no fake progress", () => {
  const html = storyLoader(STAGES);
  assert.equal((html.match(/aria-live="polite"/g) || []).length, 1);
  assert.match(html, /data-stage="0"/);
  assert.doesNotMatch(html, /100\s*%|undefined|NaN/);
  for (const s of STAGES) assert.ok(html.includes(s));
});

test("quiet loaders announce their text as a status", () => {
  const html = quietLoader("Loading the map…", "map");
  assert.match(html, /role="status"/);
  assert.match(html, /Loading the map…/);
});
