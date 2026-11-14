"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const script = fs.readFileSync(__dirname+"/../viewer/viewer.js","utf8");
const html = fs.readFileSync(__dirname+"/../viewer/index.html","utf8");
const body = script.slice(script.indexOf("  const SOURCES = ["),
  script.indexOf("  const CAMERA = {"));
const context = {Set,Map,Array,Number,Math,String,JSON,Error,console,hooks:{}};
vm.runInNewContext(body + "\nhooks.facts=episodeViewFacts;" +
  "\nhooks.count=parseViewCount;\nhooks.match=matchEpisodeFacts;" +
  "\nhooks.owner=ownerState;\nhooks.keys=FILTER_KEYS;\n",context);
const h=context.hooks;
const globalNames = ["floor_top","upper_up","plus_X","minus_X","plus_Y","minus_Y"];
function criteria(values={}, count=null) {
  return {valid:true,values,count};
}
function matches(manifest,values={},count=null) {
  return h.match(h.facts(manifest),criteria(values,count));
}
function state(frame,views,refs={},islands=[]) {
  return {frame, view_pngs:views.map(v=>"sixview/"+v+".png"),
    view_refs:refs, islands};
}
// All six existing and an island as a valid manifest scene element.
const all = {states:[
  state(0,globalNames,{},["island_0_entity_11"]),
  state(10,[],{"sixview/minus_X.png":{
    path:"sixview/minus_X.png", ref_state:0}}, ["island_0_entity_11"]),
]};
const allFacts = h.facts(all);
assert.equal(allFacts.count,6);
assert.equal(allFacts.island,true);
assert.equal(allFacts.views.size,6);
assert.equal(matches(all,{island:"yes",floor_top:"yes",upper_up:"yes"},6),true);
assert.equal(matches(all,{island:"no"}),false);
assert.equal(matches(all,{floor_top:"no"}),false);
assert.equal(matches(all,{plus_Y:"no"}),false);
assert.equal(matches(all,{upper_up:"yes"},5),false);
assert.equal(matches(all,{},6),true);

// A referenced image is a real view even when no current-frame file exists;
// a corrupt owner is not accepted.
const v3 = {states:[
  state(0,["floor_top","plus_Y"]),
  state(10,[],{
    "sixview/plus_Y.png":{path:"sixview/plus_Y.png",ref_state:0},
    "sixview/minus_X.png":{path:"sixview/minus_X.png",ref_state:0},
  }),
]};
const v3Facts=h.facts(v3);
assert.equal(v3Facts.count,2);
assert.equal(v3Facts.views.has("plus_Y"),true);
assert.equal(v3Facts.views.has("minus_X"),false);
assert.equal(matches(v3,{upper_up:"no",minus_X:"no",plus_Y:"yes",island:"no"},2),true);
assert.equal(matches(v3,{minus_X:"yes"}),false);
assert.equal(matches(v3,{island:"yes"}),false);
assert.equal(matches(v3,{},3),false);
assert.equal(h.owner(v3,1,"sixview/plus_Y.png"),0);
assert.equal(h.owner(v3,1,"sixview/minus_X.png"),null);

// The island directions never inflate the global 1–6 view count.
const islandOnly={states:[{
  frame:0,view_pngs:["islands/island_0_entity_99/plus_X.png"],
  view_refs:{},islands:["island_0_entity_99"],
}]};
assert.equal(h.facts(islandOnly).count,0);
assert.equal(h.facts(islandOnly).island,true);
assert.equal(matches(islandOnly,{island:"yes",plus_X:"no"}),true);
assert.equal(matches(islandOnly,{island:"no"}),false);
// An orphan non-existent view is not a valid Island scene.
assert.equal(h.facts({states:[{frame:0,view_pngs:[],
  islands:["something invalid"]}]}).island,false);

// Strict exact integer validation.
assert.equal(h.count("").valid,true);
assert.equal(h.count("").count,null);
for(let value=1;value<=6;value++){
  assert.equal(h.count(String(value)).valid,true);
  assert.equal(h.count(String(value)).count,value);
}
for(const bad of ["0","7","9","-1","2.1","abc","01","1e0"]){
  assert.equal(h.count(bad).valid,false,bad);
}
assert.equal(h.match(allFacts,{valid:false,count:null,values:{}}),false);

// Exactly 7 independent dropdown selectors and 1 count input.
const filterTags=[...html.matchAll(/<select data-view-filter="([^"]+)"/g)]
  .map(match=>match[1]);
assert.deepEqual(filterTags, [...globalNames,"island"]);
assert.equal(filterTags.length,7);
assert.equal((html.match(/id="view-count-filter"/g)||[]).length,1);
assert(html.includes('min="1" max="6" step="1"'));
for(const key of filterTags){
  const start=html.indexOf('<select data-view-filter="'+key+'"');
  const stop=html.indexOf("</select>",start);
  const node=html.slice(start,stop);
  assert(node.includes('<option value="any">不限</option>') &&
    node.includes('<option value="yes">包含</option>') &&
    node.includes('<option value="no">不含</option>'));
}
console.log("G2_SEVEN_INDEPENDENT_VIEW_FILTERS_V1_V2_V3_PASS");