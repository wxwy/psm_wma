"use strict";
// Fixed-root Viewer must find published Episodes from both /view/ aliases and
// the original /data1/.../view/ URL. Task counts reflect existing outputs.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const js = fs.readFileSync(__dirname + "/../viewer/viewer.js", "utf8");
const start = js.indexOf("  async function resolveDataRoot() {");
const end = js.indexOf("  function episodeDirectory() {", start);
assert(start >= 0 && end > start);
const code = js.slice(start, end);
const fixed = "/data1/data_v2_0617/robocasa365_v3_flat/" +
  "robocasa365-target-atomic-6views/";
const origin = "http://127.0.0.1:18765";
const catalog = {tasks: [
  {name: "CloseBlenderLid", count: 502, episodes: Array.from(
    {length:502}, (_,i)=>({global_id:i, local_id:i,frames:350}))},
  {name: "CloseFridge", count: 513, episodes: Array.from(
    {length:513}, (_,i)=>({global_id:i+502,local_id:i,frames:250}))},
]};
class DOMParser {
  parseFromString(html) {
    const hrefs = [...html.matchAll(/href="([^"]+)"/g)].map(m=>m[1]);
    return {querySelectorAll(){return hrefs.map(href=>({getAttribute:()=>href}));}};
  }
}
const elems = {"task-select":{value:"",disabled:true,options:[]}};
const state = {
  catalog, dataRoot:null, task:null, episode:null,
  taskScanToken:0, completedByTask:new Map(), availableCameras:new Set(),
};
const calls = {fetch:[], list:[], chosen:[]};
const context = {
  state, DOMParser, URL,
  location:{origin, href:origin+"/view/"},
  fetch: async (url) => {
    calls.fetch.push(url);
    return url === origin+"/tasks/" ?
      {ok:false,status:404} :
      {ok:true,status:200,text:async()=>'<a href="CloseBlenderLid/">a</a>' +
        '<a href="CloseFridge/">b</a>'};
  },
  listDirectory: async (path) => {
    calls.list.push(path);
    if(path.endsWith("/tasks/")) return ["CloseBlenderLid","CloseFridge"];
    if(path.includes("/CloseBlenderLid/episodes/"))
      return Array.from({length:88},(_,i)=>"episode_"+String(i).padStart(6,"0"));
    if(path.includes("/CloseFridge/episodes/")) return [];
    throw Error("unexpected task path " + path);
  },
  $: id => elems[id],
  fillSelect: (el,items,desired) => {
    el.options=items.map(([value,label])=>({value,label}));
    el.value=items.some(([value])=>value===desired)?desired:items[0]?.[0];
  },
  showStatus: () => {},
  toast: m => {throw Error(m);},
  chooseTask: async (name,previous) => {
    calls.chosen.push({name,previous});
    state.task=state.catalog.tasks.find(t=>t.name===name);
  },
  Map,Set,Promise,Array,Number,Error,console,
  hooks:{},
};
vm.runInNewContext(code +
  "\nhooks.root=resolveDataRoot;\nhooks.scan=discoverCompletedTasks;\n",context);

(async()=>{
  const root=await context.hooks.root();
  assert.equal(root,origin+fixed);
  assert.equal(calls.fetch[0],origin+"/tasks/");
  assert.equal(calls.fetch[1],origin+fixed+"tasks/");
  state.dataRoot=root;
  await context.hooks.scan();
  assert.equal(elems["task-select"].options.length,1);
  assert.equal(elems["task-select"].options[0].value,"CloseBlenderLid");
  assert.equal(elems["task-select"].options[0].label,"CloseBlenderLid · 88 EP");
  assert.equal(state.completedByTask.get("CloseBlenderLid").length,88);
  assert.equal(state.completedByTask.has("CloseFridge"),false);
  assert.equal(calls.chosen[0].name,"CloseBlenderLid");
  assert(!calls.list.some(p=>p.includes("state_")||p.includes("sixview/")),
    "must never scan per-state PNG directories");
  const priorCount=calls.fetch.length;
  context.location.href=origin+fixed+"view/";
  const longRoot=await context.hooks.root();
  assert.equal(longRoot,origin+fixed);
  assert.equal(calls.fetch.length,priorCount+1,
    "long URL must resolve output in a single directory request");
  console.log("G2_VIEWER_PUBLISHED_TASK_COUNTS_AND_ALIASES_PASS");
})().catch(e=>{console.error(e);process.exitCode=1;});