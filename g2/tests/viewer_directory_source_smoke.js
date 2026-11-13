"use strict";
const assert = require("node:assert/strict");
const api = require("../viewer/directory_picker.js");

class FakeDir {
  constructor(name) {
    this.name = name;
    this.kind = "directory";
    this.children = new Map();
    this.files = new Map();
    this.enumerated = false;
  }
  sub(name) {
    if (!this.children.has(name)) this.children.set(name, new FakeDir(name));
    return this.children.get(name);
  }
  add(path, data) {
    const names = path.split("/");
    let node = this;
    for (const part of names.slice(0, -1)) node = node.sub(part);
    const f = new Blob([typeof data === "string" ? data : JSON.stringify(data)]);
    node.files.set(names.at(-1), f);
  }
  async *entries() {
    this.enumerated = true;
    for (const [name, child] of this.children) yield [name, child];
  }
  async getFileHandle(name) {
    const file = this.files.get(name);
    if (!file) throw Object.assign(new Error("missing " + name), {name: "NotFoundError"});
    return {getFile: async () => file};
  }
  async getDirectoryHandle(name) {
    const dir = this.children.get(name);
    if (!dir) throw Object.assign(new Error("missing dir " + name), {name: "NotFoundError"});
    return dir;
  }
}
const root = new FakeDir("parent");
function addEp(dataset, task, globalId, local, complete = true) {
  const dir = dataset + "/tasks/" + task + "/episodes/episode_" +
    String(globalId).padStart(6, "0");
  const receipt = {complete, episode_id: globalId, state_count: 2};
  const manifest = {
    task_class: task, episode_id: globalId, state_count: 2,
    states: [
      {frame: 0, islands: [], view_pngs: ["sixview/floor_top.png"]},
      {frame: 10, islands: [], view_pngs: ["sixview/floor_top.png"]},
    ],
  };
  root.add(dir + "/COMPLETE.json", receipt);
  root.add(dir + "/episode_manifest.json", manifest);
  root.add(dir + "/state_000000_frame_000000/sixview/floor_top.png", "png0");
  root.add(dir + "/state_000001_frame_000010/sixview/floor_top.png", "png1");
}
addEp("dataset-A", "CloseBlenderLid", 134, 134);
addEp("dataset-B", "CloseBlenderLid", 134, 134);
addEp("dataset-B", "CloseBlenderLid", 135, 135, false);
addEp("dataset-A", "NavigateKitchen", 2022, 0);
root.add("unrelated/videos/chunk-000/something.mp4", "huge");

const catalog = {tasks: [
  {name:"CloseBlenderLid",source_dir:"CloseBlenderLid/20250822/lerobot",
   video_path:"videos/chunk-{episode_chunk:03d}/{video_key}/episode_{episode_index:06d}.mp4",
   chunks_size:1000,
   episodes:[{global_id:134,local_id:134,frames:24,instruction:"Close the blender lid"}]},
  {name:"NavigateKitchen",source_dir:"NavigateKitchen/20250822/lerobot",
   video_path:"videos/chunk-{episode_chunk:03d}/{video_key}/episode_{episode_index:06d}.mp4",
   chunks_size:1000,
   episodes:[{global_id:2022,local_id:0,frames:34,instruction:"Navigate to the counter"}]},
]};

async function testHandleScan() {
  const provider = api.createHandleProvider(root, catalog);
  const messages = [];
  const groups = await provider.scan(msg => messages.push(msg));
  assert.equal(groups.length, 3, "duplicate task groups in different datasets stay distinct");
  assert.equal(groups.reduce((n,g)=>n+g.episodes.length,0), 3);
  assert(groups.every(g=>g.episodes.length === 1));
  const blender = groups.find(g=>g.name==="CloseBlenderLid");
  assert(blender.label.includes("dataset-"));
  assert.equal(blender.episodes[0].instruction, "Close the blender lid");
  assert.equal(blender.episodes[0].frames, 24);
  const file = await provider.getFile(blender.episodes[0],
    "state_000000_frame_000000/sixview/floor_top.png");
  assert.equal(await file.text(), "png0");
  const url = await provider.getUrl(blender.episodes[0],
    "state_000000_frame_000000/sixview/floor_top.png");
  assert(url.startsWith("blob:"));
  assert.equal(messages.length, 1);
  assert.equal(root.children.get("unrelated").children.get("videos").enumerated, false,
    "must not traverse raw MP4 video directories");
  const frame = root.children.get("dataset-A").children.get("tasks")
    .children.get("CloseBlenderLid").children.get("episodes")
    .children.get("episode_000134").children.get("state_000000_frame_000000");
  assert.equal(frame.enumerated, false, "must not descend into 2 Hz images");
  provider.release();
}

async function testLegacyFilePicker() {
  const files = [];
  for (const [path, value] of [
    ["nested/tasks/CloseBlenderLid/episodes/episode_000134/COMPLETE.json",
     {complete:true,episode_id:134,state_count:2}],
    ["nested/tasks/CloseBlenderLid/episodes/episode_000134/episode_manifest.json",
     {task_class:"CloseBlenderLid",state_count:2,states:[
       {frame:0,view_pngs:["sixview/floor_top.png"]},
       {frame:10,view_pngs:["sixview/floor_top.png"]}]}],
    ["nested/tasks/CloseBlenderLid/episodes/episode_000134/state_000000_frame_000000/sixview/floor_top.png",
     "pixel"],
  ]) {
    const file = new Blob([typeof value==="string" ? value : JSON.stringify(value)]);
    file.webkitRelativePath = path;
    files.push(file);
  }
  const source = api.createFileListProvider(files,catalog);
  const groups = await source.scan();
  assert.equal(groups.length,1);
  assert.equal(groups[0].episodes.length,1);
  assert.equal(await (await source.getFile(groups[0].episodes[0],
    "state_000000_frame_000000/sixview/floor_top.png")).text(),"pixel");
  source.release();
}

async function testBadPaths() {
  const receipt = {complete:true,episode_id:12,state_count:2};
  const manifest = {state_count:2,states:[
    {frame:10,view_pngs:[]},{frame:0,view_pngs:[]}]};
  assert.equal(api.validManifest(receipt,manifest,"episode_000012"),false);
  assert.equal(api.validManifest({...receipt,complete:false},
    {...manifest,states:[{frame:0,view_pngs:[]},{frame:10,view_pngs:[]}]},
    "episode_000012"),false);
  assert.equal(api.resolveTask(
    ["data","tasks","CloseBlenderLid","episodes","episode_000134"],
    {task_class:"UntrustedWrongTask"}).name, "CloseBlenderLid");
}
(async () => {
  await testHandleScan();
  await testLegacyFilePicker();
  await testBadPaths();
  console.log("G2_DIRECTORY_NATIVE_RECURSIVE_DISCOVERY_PASS");
})().catch(error => {console.error(error);process.exitCode=1;});