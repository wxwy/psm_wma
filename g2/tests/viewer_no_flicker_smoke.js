"use strict";
// The viewer must never blank a visible map while a new PNG is decoding.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source = fs.readFileSync(__dirname + "/../viewer/viewer.js", "utf8");
const begin = source.indexOf("  function decodedImage(path) {");
const end = source.indexOf("  function updateTimeline() {", begin);
assert(begin >= 0 && end > begin);
const snippet = source.slice(begin, end);

const pending = new Map();
class DelayedImage {
  constructor() {
    this.naturalWidth = 640;
    this.naturalHeight = 480;
  }
  set src(path) {
    this.path = path;
    pending.set(path, this);
  }
  decode() {
    return new Promise(resolve => { this.finishDecode = resolve; });
  }
}
const drawn = [];
const canvas = {
  width: 640, height: 480, hidden: false,
  getContext() {
    return {drawImage(image) {drawn.push(image.path);}};
  },
};
const tile = {
  source: "floor_top", video: null, status: {textContent: ""},
  displayedPath: "previous-frame.png", canvas,
  fallback: {hidden: true}, fallbackText: {textContent: ""},
  generation: 0, disposed: false,
};
const state = {
  manifest: {states: [{frame: 0},{frame: 10},{frame: 20}]},
  media: [tile], preload: new Map(),
};
const hooks = {};
const context = {state, Image: DelayedImage, hooks,
  viewPath: (kind, index) => "frame_" + index + ".png",
  pad: n => String(n).padStart(6, "0"),
  Promise, Map, Set, Math, Error, console,
};
vm.runInNewContext(snippet + "\nhooks.displayFrame=displayFrame;\n", context);
const flush = () => new Promise(resolve => setImmediate(resolve));

async function finish(path) {
  const image = pending.get(path);
  assert(image, "missing preload: " + path);
  image.onload();
  assert(image.finishDecode);
  image.finishDecode();
  await flush();
}

async function main() {
  hooks.displayFrame(1);
  assert.equal(tile.displayedPath, "previous-frame.png");
  assert.equal(tile.canvas.hidden, false);
  assert.deepEqual(drawn, []);
  // Scrub ahead while the previous requested PNG is still decoding.
  hooks.displayFrame(2);
  await finish("frame_1.png");
  assert.equal(tile.displayedPath, "previous-frame.png");
  assert.deepEqual(drawn, [], "stale PNG must not paint");
  await finish("frame_2.png");
  assert.equal(tile.displayedPath, "frame_2.png");
  assert.deepEqual(drawn, ["frame_2.png"]);
  assert.equal(tile.fallback.hidden, true);
  // A late completed download after a layout rebuild cannot mutate tiles.
  hooks.displayFrame(1);
  tile.disposed = true;
  await finish("frame_1.png");
  assert.deepEqual(drawn, ["frame_2.png"]);
  console.log("VIEWER_NO_BLANK_FRAME_REGRESSION_PASS");
}
main().catch(e => {console.error(e);process.exitCode = 1;});