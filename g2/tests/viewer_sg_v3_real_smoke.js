"use strict";
// Integration of unchanged Viewer viewPath/islandGroups with v3 physical+ref PNG
// inventory. SG references are resolved by Python, not the image viewer.
const assert=require("node:assert/strict");
const fs=require("node:fs");
const pathLib=require("node:path");
const vm=require("node:vm");
const episode=process.argv[2];
assert(episode && fs.existsSync(episode),"expected a completed real v3 Episode");
const manifest=JSON.parse(
  fs.readFileSync(pathLib.join(episode,"episode_manifest.json"),"utf8")
);
assert.equal(manifest.schema,"g2_atomic_compact_6views_v3");
assert(manifest.indexed_sg_enabled===true);
const js=fs.readFileSync(pathLib.join(__dirname,"../viewer/viewer.js"),"utf8");
const groups=js.slice(js.indexOf("  const SOURCES = ["),js.indexOf("  const CAMERA = {"));
const path=js.slice(js.indexOf("  function viewPath(source, index) {"),
                    js.indexOf("  function spatialAt(time) {"));
const root="/tasks/T/episodes/episode_000011/";
const state={manifest};
const scope={state,console,document:{},Set,Map,Error,
  episodeDirectory:()=>root,
  pad:n=>String(n).padStart(6,"0")};
vm.runInNewContext(groups+path+"\nstateHooks={viewPath,islandGroups};",scope);
const h=scope.stateHooks;
let inspected=0, refs=0;
for (let i=0;i<manifest.states.length;i++) {
  const row=manifest.states[i];
  const paths=[...row.view_pngs,...Object.keys(row.view_refs)];
  for (const rel of paths) {
    const bits=rel.split("/");
    const source=bits[0]==="islands"
      ?"island:"+bits[1]+":"+bits[2].slice(0,-4)
      :bits.slice(-1)[0].slice(0,-4);
    const uri=h.viewPath(source,i);
    assert(uri && uri.startsWith(root),"missing source "+i+" "+rel);
    const local=pathLib.join(episode,uri.slice(root.length));
    assert(fs.statSync(local).isFile(),"broken image ref "+i+" "+rel+" "+uri);
    inspected++;
    if (Object.hasOwn(row.view_refs,rel))refs++;
  }
}
assert(inspected>refs && refs>0);
console.log("P3_V3_VIEWER_REAL_EPISODE_ALL_IMAGES_PASS",{
  states:manifest.states.length,views:inspected,referenced:refs,
  source:episode,
});
