"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
const js=fs.readFileSync(__dirname+"/../viewer/viewer.js","utf8");
const groups=js.slice(js.indexOf("  const SOURCES = ["),js.indexOf("  const CAMERA = {"));
const path=js.slice(js.indexOf("  function viewPath(source, index) {"),
                    js.indexOf("  function spatialAt(time) {"));
assert(groups.includes("function islandGroups"));
assert(path.includes("function viewPath"));
const manifest={
  schema:"g2_atomic_compact_6views_v2",
  states:[
    {frame:0,view_pngs:["sixview/floor_top.png","sixview/plus_X.png",
       "islands/island_0_entity_11/plus_Y.png"],
     view_refs:{},islands:["island_0_entity_11"]},
    {frame:10,view_pngs:["sixview/floor_top.png"],
     view_refs:{
      "sixview/plus_X.png":{ref_state:0,path:"sixview/plus_X.png"},
      "islands/island_0_entity_11/plus_Y.png":
       {ref_state:0,path:"islands/island_0_entity_11/plus_Y.png"}},
     islands:["island_0_entity_11"]},
    {frame:20,view_pngs:[],
     view_refs:{
      "sixview/floor_top.png":{ref_state:1,path:"sixview/floor_top.png"},
      "sixview/plus_X.png":{ref_state:0,path:"sixview/plus_X.png"},
      "islands/island_0_entity_11/plus_Y.png":
       {ref_state:0,path:"islands/island_0_entity_11/plus_Y.png"}},
     islands:["island_0_entity_11"]},
  ],
};
const state={manifest};
const scope={state,console,document:{},Set,Map,Error,
              episodeDirectory:()=>"/tasks/T/episodes/episode_000134/",
              pad:n=>String(n).padStart(6,"0")};
vm.runInNewContext(groups+path+
  "\nstateHooks={viewPath,islandGroups};",scope);
const h=scope.stateHooks;
assert.equal(h.viewPath("floor_top",0),
 "/tasks/T/episodes/episode_000134/state_000000_frame_000000/sixview/floor_top.png");
assert.equal(h.viewPath("floor_top",1),
 "/tasks/T/episodes/episode_000134/state_000001_frame_000010/sixview/floor_top.png");
assert.equal(h.viewPath("floor_top",2),
 "/tasks/T/episodes/episode_000134/state_000001_frame_000010/sixview/floor_top.png");
assert.equal(h.viewPath("plus_X",2),
 "/tasks/T/episodes/episode_000134/state_000000_frame_000000/sixview/plus_X.png");
assert.equal(h.viewPath("island:island_0_entity_11:plus_Y",2),
 "/tasks/T/episodes/episode_000134/state_000000_frame_000000/islands/island_0_entity_11/plus_Y.png");
assert.equal(h.islandGroups(manifest).length,1);
assert.equal(h.islandGroups(manifest)[0].choices[0].value,
 "island:island_0_entity_11:plus_Y");

const corrupt=manifest.states[2];
corrupt.view_refs["sixview/plus_X.png"]={ref_state:2,path:"sixview/plus_X.png"};
assert.equal(h.viewPath("plus_X",2),null);
corrupt.view_refs["sixview/plus_X.png"]={ref_state:1,path:"sixview/plus_X.png"};
assert.equal(h.viewPath("plus_X",2),null);  // no chained refs
corrupt.view_refs["sixview/plus_X.png"]={ref_state:0,path:"islands/../escape.png"};
assert.equal(h.viewPath("plus_X",2),null);
assert.equal(h.viewPath("right",2),null);
console.log("P1_INDEXED_VIEWER_DIRECT_REF_AND_V1_COMPAT_SMOKE_PASS");
