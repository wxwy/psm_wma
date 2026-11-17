"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const code = fs.readFileSync(__dirname + "/../viewer/viewer.js", "utf8");
const root = process.argv[2];
assert(root, "pass a real synthetic Stage-A package root");
const complete = JSON.parse(fs.readFileSync(root + "/COMPLETE.json", "utf8"));
const manifest = JSON.parse(fs.readFileSync(root + "/episode_manifest.json", "utf8"));
const declarations = code.slice(code.indexOf("  const SOURCES = ["), code.indexOf("  const CAMERA = {"));
const load = code.slice(code.indexOf("  async function loadEpisode("), code.indexOf("  function setViewFilterStatus("));
const paths = code.slice(code.indexOf("  function viewPath("), code.indexOf("  function spatialAt("));
const nodes = new Map();
const messages = [];
const state = {
  task: {name: manifest.task_class, episodes: [{global_id: manifest.episode_id, frames: 21}]},
  catalog: {source_fps: 20}, token: 0, availableCameras: new Set(), preload: new Map(), autoLayout: false,
};
let corruptHeader = false;
const context = {
  state, Set, Map, Array, Number, Math, String, JSON, Error, Promise,
  $: id => {
    if (!nodes.has(id)) nodes.set(id, {removeAttribute() {}, load() {}});
    return nodes.get(id);
  },
  pause() {}, transportEnabled() {}, renderLayout() {}, seek() {},
  showStatus: (message, kind) => messages.push({message, kind}),
  toast: message => messages.push({error: message}),
  episodeDirectory: () => root + "/", fmt: String, pad: n => String(n).padStart(6, "0"),
  detectAvailableCameras: async () => new Set(),
  fetchJson: async path => {
    if (path.endsWith("COMPLETE.json")) {
      const value = {...complete};
      if (corruptHeader) delete value.state_count;
      return value;
    }
    if (path.endsWith("episode_manifest.json")) return manifest;
    throw Error("unexpected fetch " + path);
  },
  hooks: {},
};
vm.runInNewContext(declarations + paths + load + "\nhooks.load=loadEpisode;hooks.path=viewPath;", context);
(async () => {
  await context.hooks.load(manifest.episode_id);
  assert(state.manifest, JSON.stringify(messages));
  assert.equal(messages.at(-1).kind, "ready");
  assert(context.hooks.path("floor_top", 2).includes("state_000000_frame_000000/sixview/floor_top.png"));
  assert(context.hooks.path("floor_top_w_rbs", 2).includes("state_000001_frame_000010/sixview/floor_top_w_rbs.png"));
  corruptHeader = true;
  await context.hooks.load(manifest.episode_id);
  assert.equal(state.manifest, null);
  assert(messages.some(message => message.error?.includes("尚未完整生成")));
  console.log("G2_STAGE_A_ACTUAL_LOAD_EPISODE_HEADER_AND_OWNER_PASS");
})().catch(error => {console.error(error); process.exitCode = 1;});
