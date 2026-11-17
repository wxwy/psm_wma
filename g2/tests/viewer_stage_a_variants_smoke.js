"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const script = fs.readFileSync(__dirname + "/../viewer/viewer.js", "utf8");
const body = script.slice(script.indexOf("  const SOURCES = ["), script.indexOf("  const CAMERA = {"));
const context = {Set, Map, Array, Number, Math, String, JSON, Error, hooks: {}};
vm.runInNewContext(body + "\nhooks.facts=episodeViewFacts; hooks.sources=availableSources; hooks.valid=validSource; hooks.meta=sourceMetadata;", context);
const h = context.hooks;
const manifest = {schema: "g2_spatial_profile_episode_v1", states: [
  {frame: 0, view_pngs: [
    "sixview/rooms/0/floor_top.png", "sixview/rooms/0/floor_top_w_rbs.png",
    "sixview/rooms/1/floor_top.png", "sixview/rooms/1/floor_top_w_rbs.png",
    "sixview/rooms/0/plus_X.png"
  ], view_refs: {}},
  {frame: 10, view_pngs: ["sixview/rooms/0/floor_top_w_rbs.png"], view_refs: {
    "sixview/rooms/0/floor_top.png": {ref_state: 0, path: "sixview/rooms/0/floor_top.png"}
  }}
]};
assert.equal(h.facts(manifest).count, 2); // floor_top plus_X, never a seventh direction.
assert.equal(h.facts(manifest).views.has("floor_top_w_rbs"), false);
const sources = h.sources(manifest).flatMap(g => g.sources.map(s => s[0]));
assert(sources.includes("room:0:floor_top"));
assert(sources.includes("room:0:floor_top_w_rbs"));
assert(sources.includes("room:1:floor_top_w_rbs"));
assert(h.valid("floor_top_w_rbs"));
assert(h.valid("room:1:floor_top_w_rbs"));
assert(!h.valid("room:../1:floor_top"));
assert(h.meta("room:1:floor_top_w_rbs")[1].includes("Room 1"));
assert(h.sources({states:[{frame:0,view_pngs:["sixview/floor_top_w_rbs.png"],view_refs:{}}]})[0].sources.some(s => s[0]==="floor_top_w_rbs"));
console.log("G2_STAGE_A_DUAL_VARIANT_MULTIROOM_CANONICAL_COUNT_PASS");
