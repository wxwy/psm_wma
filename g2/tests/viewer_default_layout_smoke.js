"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

// Test the actual default-layout and storage-migration functions from Viewer,
// not a duplicate implementation in the test.
const js = fs.readFileSync(__dirname + "/../viewer/viewer.js", "utf8");
const first = js.slice(js.indexOf("  const SOURCES = ["),
  js.indexOf("  const CAMERA = {"));
const second = js.slice(js.indexOf("  const STORAGE = "),
  js.indexOf("  const state = {"));
assert(first.includes("function availableSources"));
assert(second.includes("function startingLayout"));
const items = new Map();
let nextID = 0;
const store = {
  getItem(key) {return items.get(key) ?? null;},
  setItem(key, value) {items.set(key, value);},
  removeItem(key) {items.delete(key);},
};
const hooks = {};
const context = {
  crypto: {randomUUID: () => "id-" + (++nextID)},
  localStorage: store, hooks, console, JSON, Set, Map, Array, Number,
};
vm.runInNewContext(first + second +
  "\nhooks.starting=startingLayout;hooks.read=readLayout;" +
  "\nhooks.legacy=isLegacyDefault;hooks.valid=validSavedLayout;\n", context);
const h = hooks;
const rowSources = rows => Array.from(rows, row =>
  Array.from(row.blocks, b => b.source));
const cameras = new Set(["left", "right", "wrist"]);
const island = "island_0_entity_11";
const roomViews = ["floor_top", "plus_Y", "plus_X",
  "minus_Y", "minus_X", "upper_up"];
const islandPaths = ["plus_X", "minus_X", "plus_Y", "minus_Y"]
  .map(direction => "islands/" + island + "/" + direction + ".png");
const full = {states:[
  {frame:0, islands:[island],
   view_pngs:[...roomViews.map(v=>"sixview/"+v+".png"), ...islandPaths]},
  {frame:10, islands:[island], view_pngs:[],
   view_refs:Object.fromEntries(islandPaths.map(path=>[path,{path,ref_state:0}]))},
]};
const rich = rowSources(h.starting(full,cameras));
assert.equal(rich.length, 3);
assert.deepEqual(rich[0], ["left","right","wrist"]);
assert.deepEqual(rich[1], ["floor_top","plus_Y","plus_X"]);
assert.deepEqual(rich[2], ["plus_X","minus_X","plus_Y","minus_Y"]
  .map(d=>"island:"+island+":"+d));
assert.equal(new Set(rich.flat()).size, 10);

// No Island: third row falls back to remaining real room views, then reuses
// a real view for its fourth slot. Never proposes an absent Island direction.
const noIsland = {states:[
  {frame:0,islands:[],view_pngs:roomViews.map(v=>"sixview/"+v+".png")},
]};
const nonIslandRows = rowSources(h.starting(noIsland,cameras));
assert.equal(nonIslandRows.length,3);
assert.deepEqual(nonIslandRows[0],["left","right","wrist"]);
assert.deepEqual(nonIslandRows[1],["floor_top","plus_Y","plus_X"]);
assert.deepEqual(nonIslandRows[2],
  ["minus_Y","minus_X","upper_up","floor_top"]);

// Sparse scene and only a subset of videos: every default source is actually
// available in this Episode, with fixed row lengths 3/3/4.
const sparse = {states:[{frame:0,islands:[],
  view_pngs:["sixview/floor_top.png","sixview/plus_Y.png"]}]};
const sparseRows = rowSources(h.starting(sparse,new Set(["left","wrist"])));
assert.deepEqual(sparseRows.map(row=>row.length), [3,3,4]);
const actual = new Set(["floor_top","plus_Y","left","wrist"]);
assert(sparseRows.flat().every(s=>actual.has(s)));

// Partial Island: use just its existing directions and fill remaining slots
// with the fallback room/global camera list.
const partial = {states:[{frame:0,islands:[island],
  view_pngs:["sixview/floor_top.png","sixview/plus_X.png",
    "islands/"+island+"/plus_X.png","islands/"+island+"/minus_Y.png"]}]};
const partialRows = rowSources(h.starting(partial,cameras));
assert.equal(partialRows[2][0],"island:"+island+":plus_X");
assert.equal(partialRows[2][1],"island:"+island+":minus_Y");
assert(partialRows[2].every(s=>!s.includes("island:"+island+":minus_X")));

// Before selecting an Episode there are still three provisional rows.
assert.deepEqual(rowSources(h.starting()).map(row=>row.length),[3,3,4]);

// Stored legacy two-row *default* is automatically migrated to three rows;
// separately saved custom arrangements must not be overwritten.
const legacyDefault = [
  {id:"legacy-1",blocks:["floor_top","left","wrist"].map(
    (source,i)=>({id:"leg-a-"+i,source}))},
  {id:"legacy-2",blocks:["plus_X","minus_X","plus_Y"].map(
    (source,i)=>({id:"leg-b-"+i,source}))},
];
store.setItem("psm-g2-viewer-layout-v1",JSON.stringify(legacyDefault));
assert.equal(h.read().auto,true);
assert.equal(h.read().rows.length,3);
const custom = [{id:"custom-row",blocks:[
  {id:"custom-one",source:"minus_Y"},
  {id:"custom-two",source:"left"},
]}];
store.setItem("psm-g2-viewer-layout-v1",JSON.stringify(custom));
assert.equal(h.read().auto,false);
assert.deepEqual(rowSources(h.read().rows),[["minus_Y","left"]]);
store.setItem("psm-g2-viewer-layout-v2","auto");
assert.equal(h.read().auto,true);
assert.equal(h.read().rows.length,3);
store.setItem("psm-g2-viewer-layout-v2",JSON.stringify(custom));
assert.equal(h.read().auto,false);
assert.deepEqual(rowSources(h.read().rows),[["minus_Y","left"]]);
assert(h.valid(custom));

// One-click reset URL overrides old layout exactly once.
const resetURL="http://127.0.0.1:18765/view/?reset_layout=1&v=20261114-force-3rows";
context.URL=URL;
context.location={href:resetURL};
let replacedURL=null;
context.history={replaceState(_state,_title,url){
  replacedURL=url;
  context.location.href="http://127.0.0.1:18765"+url;
}};
const recovered=h.read();
assert.equal(recovered.auto,true);
assert.equal(recovered.rows.length,3);
assert.equal(store.getItem("psm-g2-viewer-layout-v2"),"auto");
assert(replacedURL.includes("v=20261114-force-3rows"));
assert(!replacedURL.includes("reset_layout"));
store.setItem("psm-g2-viewer-layout-v2",JSON.stringify(custom));
assert.equal(h.read().auto,false,
  "manual changes after a one-shot reset must survive future reloads");
assert.deepEqual(rowSources(h.read().rows),[["minus_Y","left"]]);

assert(js.includes("if (state.autoLayout)"));
assert(js.includes("state.rows = startingLayout(manifest, cameras);"));
assert(js.includes("resetDefaultLayout();"));
assert(js.includes('toast("已恢复默认三行布局")'));
console.log("G2_DEFAULT_THREE_ROWS_DYNAMIC_ISLAND_AND_LAYOUT_MIGRATION_PASS");