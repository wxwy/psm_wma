"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source = fs.readFileSync(__dirname + "/../viewer/viewer.js", "utf8");
const declarations = source.slice(
  source.indexOf("  const SOURCES = ["),
  source.indexOf("  const CAMERA = {"));
const begin = source.indexOf("  function setViewFilterStatus(");
const end = source.indexOf("  async function chooseTask(", begin);
assert(begin >= 0 && end > begin);
const filters = source.slice(begin, end);
const keys = ["floor_top","upper_up","plus_X","minus_X","plus_Y","minus_Y","island"];
const selects = keys.map(key => ({
  dataset: {viewFilter:key,filterValue:"any"},
  value:"any",
}));
const input = {value:"",attributes:{},
  setAttribute(name,value) {this.attributes[name]=value;}};
const picker = {disabled:true,value:"",options:[]};
const elements = {
  "view-filter-status":{textContent:"",className:""},
  "view-count-filter":input,
  "episode-select":picker,
  "available-count":{textContent:""},
  "instruction-text":{textContent:""},
};
const task = {name:"CloseBlenderLid"};
const episodes = Array.from({length:24},(_,i)=>({
  global_id:i,local_id:i,frames:100,
}));
const state = {
  task, catalog:{source_fps:20}, dataRoot:"http://host/output/",
  token:0,filterToken:0,episode:null,manifest:null,
  completedByTask:new Map([[task.name,episodes]]),
  episodeFactsCache:new Map(),filteredEpisodes:[],
  availableCameras:new Set(),
};
const received={calls:[],loaded:[]};
let concurrent=0,peak=0;
function fakeManifest(index) {
  const views = index % 2 === 0 ? ["floor_top","plus_Y"] : ["floor_top"];
  return {states:[{frame:0,
    islands:index%3===0?["island_0_entity_11"]:[],
    view_pngs:views.map(x=>"sixview/"+x+".png")}]};
}
const controls = {
  state,
  document:{querySelectorAll() {return selects;}},
  $: id => elements[id],
  fetchJson:async url=>{
    received.calls.push(url);
    concurrent++;
    peak=Math.max(peak,concurrent);
    await new Promise(resolve=>setTimeout(resolve,1));
    concurrent--;
    const match = url.match(/episode_(\d+)\/episode_manifest.json$/);
    assert(match,"only manifest files may be fetched by filters: "+url);
    return fakeManifest(Number(match[1]));
  },
  pause:()=>{},transportEnabled:()=>{},renderLayout:()=>{},
  loadEpisode:async id=>{
    received.loaded.push(id);
    state.episode=episodes.find(e=>e.global_id===id);
  },
  fillSelect:(select,values,desired)=>{
    select.options=values.map(([value,label])=>({value:String(value),label}));
    select.value=values.some(([value])=>String(value)===String(desired))?
      String(desired):String(values[0]?.[0]??"");
  },
  fmt:n=>String(n),
  pad:n=>String(n).padStart(6,"0"),
  Set,Map,Array,Number,Promise,Math,JSON,Error,console,
  hooks:{},
};
vm.runInNewContext(declarations + filters +
  "\nhooks.refresh=refreshEpisodes;\nhooks.criteria=readViewCriteria;\n",
  controls);
const {refresh} = controls.hooks;
function selectValue(key,value) {
  selects.find(s=>s.dataset.viewFilter===key).value=value;
}
async function run() {
  await refresh();
  assert.equal(received.calls.length,0,
    "no active criteria should not scan any manifest");
  assert.equal(picker.options.length,24);
  selectValue("floor_top","yes");
  selectValue("island","no");
  input.value="2";
  await refresh();
  const wanted=[2,4,8,10,14,16,20,22];
  assert.deepEqual(state.filteredEpisodes.map(e=>e.global_id),wanted);
  assert.equal(picker.options.length,8);
  assert(elements["available-count"].textContent.includes("8"));
  assert.equal(input.attributes["aria-invalid"],"false");
  assert(peak <= 10,"concurrency must not exceed 10");
  assert.equal(received.calls.length,24);
  selectValue("floor_top","any");
  selectValue("island","yes");
  selectValue("plus_Y","no");
  input.value="1";
  await refresh();
  assert.deepEqual(state.filteredEpisodes.map(e=>e.global_id),[3,9,15,21]);
  assert.equal(received.calls.length,24,
    "re-selecting filters must use cached per-Episode facts");
  input.value="7";
  await refresh();
  assert.equal(picker.disabled,true);
  assert.equal(input.attributes["aria-invalid"],"true");
  assert(elements["view-filter-status"].textContent.includes("1–6"));
  input.value="";
  selects.forEach(s=>s.value="any");
  await refresh();
  assert.equal(state.filteredEpisodes.length,24);
  assert.equal(received.calls.length,24);
  console.log("G2_VIEWER_EPISODE_FILTER_UI_ASYNC_CACHED_INTEGRATION_PASS");
}
run().catch(error=>{console.error(error);process.exitCode=1;});