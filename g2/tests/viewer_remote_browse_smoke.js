"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const source = fs.readFileSync(__dirname + "/../viewer/viewer.js", "utf8");
const from = source.indexOf("  async function remoteDirectoryEntries(url) {");
const until = source.indexOf("  async function discoverHttpFolders(initialUrl) {", from);
assert(from > 0 && until > from);
const snippet = source.slice(from, until);
const rootUrl = "http://localhost:18765/data1/robocasa365-target-atomic-6views/";
const page = rootUrl + "view/";
const pages = new Map([
  [rootUrl, '<html><a href="../">Parent</a><a href="tasks/">tasks</a>' +
    '<a href="view/">view</a><a href="bad%2Fchild/">invalid</a></html>'],
  ["http://localhost:18765/data1/", '<html><a href="../">Parent</a>' +
    '<a href="robocasa365-target-atomic-6views/">dataset</a></html>'],
  [rootUrl + "tasks/", '<html><a href="../">Parent</a>' +
    '<a href="CloseBlenderLid/">CloseBlenderLid</a></html>'],
]);
const httpCalls = [];
function mockAnchor(href) {return {getAttribute: name => name === "href" ? href : ""};}
class DOMParser {
  parseFromString(html) {
    return {
      querySelectorAll(name) {
        assert.equal(name, "a[href]");
        return [...html.matchAll(/href="([^"]+)"/g)].map(m => mockAnchor(m[1]));
      },
    };
  }
}
const elements = {
  "remote-path": {value:rootUrl},
  "server-directory-select": {disabled:true, options:[], value:""},
  "server-browse-status": {textContent:""},
};
const state = {serverBrowseToken:0, serverBrowseEntries:[]};
const hooks = {};
const loc = {href:page,origin:"http://localhost:18765"};
const context = {
  state, hooks, DOMParser, URL, location:loc,
  $: id => elements[id],
  fillSelect(select, options, preferred) {
    select.options = options.map(pair => ({value:String(pair[0]), label:pair[1]}));
    select.value = String(preferred);
  },
  toast(message) {throw Error(message);},
  async fetch(url) {
    const u = url.toString(); httpCalls.push(u);
    if (!pages.has(u)) return {ok:false,status:404,text:async()=>""};
    return {ok:true,status:200,text:async()=>pages.get(u)};
  },
};
vm.runInNewContext(snippet +
  "\nhooks.list = listServerDirectoryChoices;" +
  "\nhooks.parent = navigateServerParent;" +
  "\nhooks.canonical = canonicalServerRoot;" +
  "\nhooks.entries = remoteDirectoryEntries;\n", context);
const h=hooks;
(async()=>{
  await h.list();
  assert.equal(elements["server-directory-select"].disabled,false);
  assert.equal(state.serverBrowseEntries.length,2);
  assert.equal(state.serverBrowseEntries[0].name,"tasks");
  assert.equal(elements["server-directory-select"].options.length,3);
  assert(elements["server-browse-status"].textContent.includes("2 个子目录"));
  const entered=state.serverBrowseEntries[0].url;
  assert.equal(entered,rootUrl+"tasks/");
  elements["remote-path"].value=new URL(entered).pathname;
  await h.list();
  assert.equal(state.serverBrowseEntries.length,1);
  assert.equal(state.serverBrowseEntries[0].name,"CloseBlenderLid");
  h.parent();
  assert.equal(elements["remote-path"].value,new URL(rootUrl).pathname);
  await new Promise(r=>setImmediate(r));
  assert.equal(state.serverBrowseEntries.length,2);
  assert.equal(h.canonical("/mnt/data1/myfolder/"),"http://localhost:18765/data1/myfolder/");
  assert.throws(()=>h.canonical("https://evil.example/file/"),/同源/);
  assert.equal(httpCalls.length,3);
  console.log("G2_SERVER_HIERARCHICAL_DROPDOWN_PASS");
})().catch(e=>{console.error(e);process.exitCode=1;});