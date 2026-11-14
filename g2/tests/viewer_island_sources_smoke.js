"use strict";
// Island candidates must reflect exactly the original per-state manifest.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const js = fs.readFileSync(__dirname + "/../viewer/viewer.js", "utf8");
const begin = js.indexOf("  const SOURCES = [");
const end = js.indexOf("  const CAMERA = {", begin);
assert(begin > -1 && end > begin);
const groups = js.slice(begin, end);
const startPath = js.indexOf("  function viewPath(source, index) {");
const endPath = js.indexOf("  function spatialAt(time) {", startPath);
assert(startPath >= 0 && endPath > startPath);
const pathSource = js.slice(startPath, endPath);
const nodes = [];
function makeElement(tag) {
  const el = {
    tag, children: [], disabled: false, value: "", textContent: "", label: "",
    append(child) {this.children.push(child);},
    replaceChildren(...items) {this.children = items;},
    querySelectorAll(name) {
      return this.children.flatMap(ch => ch.tag === name ? [ch] :
        ch.querySelectorAll ? ch.querySelectorAll(name) : []);
    },
  };
  nodes.push(el);
  return el;
}
const doc = {createElement: makeElement};
const manifest = {
  states: [
    {frame: 0, islands: ["island_0_entity_11", "island_0_entity_110"],
     view_pngs: ["sixview/floor_top.png",
       "islands/island_0_entity_11/plus_X.png",
       "islands/island_0_entity_11/minus_X.png",
       "islands/island_0_entity_11/plus_Y.png",
       "islands/island_0_entity_11/minus_Y.png",
       "islands/island_0_entity_110/plus_X.png",
       "islands/island_0_entity_110/minus_X.png",
       "islands/island_0_entity_110/plus_Y.png",
       "islands/island_0_entity_110/minus_Y.png"]},
    {frame: 10, islands: ["island_0_entity_11"],
     view_pngs: ["sixview/floor_top.png",
       "islands/island_0_entity_11/plus_X.png",
       "islands/island_0_entity_11/minus_X.png",
       "islands/island_0_entity_11/plus_Y.png",
       "islands/island_0_entity_11/minus_Y.png"]},
  ],
};
const scope = {
  document: doc, state: {manifest, availableCameras: new Set(["left", "right", "wrist"])}, hooks: {},
  episodeDirectory: () => "../tasks/example/episodes/episode_000134/",
  pad: n => String(n).padStart(6,"0"),
  Map, Set, Error, console,
};
vm.runInNewContext(groups + pathSource +
  "\nhooks.groups=islandGroups;\nhooks.select=fillSourceSelect;" +
  "\nhooks.viewPath=viewPath;\nhooks.parse=parseIslandSource;" +
  "\nhooks.available=availableSources;" +
  "\nhooks.valid=validSource;\n",scope);
const h = scope.hooks;
const result = h.groups(manifest);
assert.equal(result.length, 2);
assert.equal(result[0].id, "island_0_entity_11");
assert.equal(result[1].id, "island_0_entity_110");
assert.deepEqual(Array.from(result[0].choices, o => o.label),
  ["+X", "−X", "+Y", "−Y"]);
for(const island of result) assert.equal(island.choices.length,4);
let selected = "island:island_0_entity_11:minus_Y";
const select = makeElement("select");
h.select(select, selected);
assert.equal(select.value, selected);
assert.equal(select.querySelectorAll("optgroup").length,4);
assert.equal(select.querySelectorAll("option").length,12);
assert.deepEqual(Array.from(select.querySelectorAll("option")
  .filter(o => !o.value.startsWith("island:")), o => o.value),
  ["floor_top", "left", "right", "wrist"]);
assert(!select.querySelectorAll("option").some(o => o.value === "plus_X"));
assert(!select.querySelectorAll("option").some(o => o.value === "upper_up"));
assert(h.valid(selected));
assert(!h.valid("island:../../etc:plus_X"));
assert(!h.valid("island:island_0_entity_11:upper_up"));
assert.equal(h.viewPath(selected,0),
  "../tasks/example/episodes/episode_000134/state_000000_frame_000000/" +
  "islands/island_0_entity_11/minus_Y.png");
assert.equal(h.viewPath("island:island_0_entity_110:plus_X",1),null);
assert.equal(h.viewPath("plus_X",0),null);
assert.equal(h.viewPath("floor_top",0),
  "../tasks/example/episodes/episode_000134/state_000000_frame_000000/sixview/floor_top.png");
// On Episode change, unavailable Island options disappear; the old selected
// source falls back to one actually present in the new Episode.
scope.state.manifest = {states:[{frame:0,islands:[],view_pngs:["sixview/floor_top.png"]}]};
assert.equal(h.groups(scope.state.manifest).length,0);
const absentSelect=makeElement("select");
h.select(absentSelect,selected);
assert.equal(absentSelect.value,"floor_top");
assert.equal(absentSelect.querySelectorAll("optgroup").length,2);
assert.equal(absentSelect.querySelectorAll("option").length,4);
assert(!absentSelect.querySelectorAll("option").some(o => o.value===selected));
assert.equal(h.viewPath(selected,0),null);
// All sources must disappear if no view PNGs and no accessible cameras exist.
scope.state.manifest = {states:[{frame:0,islands:[],view_pngs:[]}]};
scope.state.availableCameras = new Set();
const empty = makeElement("select");
assert.equal(h.select(empty,"floor_top"),null);
assert.equal(empty.disabled,true);
assert.equal(empty.querySelectorAll("option").length,1);
assert.equal(h.available(scope.state.manifest, new Set()).length,0);
// Malicious forged Island IDs and unreferenced directions must not be offered.
const corrupted = {states:[{frame:0,islands:["../secret","island_1_entity_9"],
 view_pngs:["islands/../secret/plus_X.png",
 "islands/island_1_entity_9/minus_X.png"]}]};
assert.equal(h.groups(corrupted).length,1);
assert.equal(h.groups(corrupted)[0].choices.length,1);
console.log("VIEWER_ISLAND_FOUR_VIEW_CONTRACT_PASS");