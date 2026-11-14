"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source = fs.readFileSync(__dirname + "/../viewer/viewer.js", "utf8");
const start = source.indexOf("  function waitForClockSeek(video) {");
const end = source.indexOf("  function decodedImage(path) {", start);
assert(start >= 0 && end > start);
const actual = source.slice(start, end);

class FakeClock {
  constructor() {
    this.duration=18.05;this.readyState=1;this.seeking=false;this.paused=true;
    this.ended=true;this._time=18.05;this.events=new Map();
    this.playCalls=[];this.pauseCalls=0;
  }
  get currentTime() {return this._time;}
  set currentTime(value) {
    this._time=value;this.seeking=true;this.ended=false;
  }
  addEventListener(name, cb) {
    if (!this.events.has(name)) this.events.set(name,new Set());
    this.events.get(name).add(cb);
  }
  removeEventListener(name, cb) {this.events.get(name)?.delete(cb);}
  emit(name) {
    if (name==="seeked")this.seeking=false;
    for (const cb of [...(this.events.get(name) || [])]) cb();
  }
  async play() {
    assert(!this.seeking, "Left clock must NOT play while still seeking");
    this.playCalls.push(this.currentTime);
    this.paused=false;
  }
  pause(){this.paused=true;this.pauseCalls++;}
}
const clock = new FakeClock();
const state = {
  manifest:{states:[{frame:0}]},time:18.05,duration:18.05,
  playing:false,playGeneration:0,frameHandle:null,
  fallbackTime:0,fallbackStart:0,clockFailed:false,
};
const callbacks=[],ticks=[],notes=[],followerCalls=[],seeks=[];
const fakeTime={
  timer:0,timers:new Map(),
  setTimeout(callback) {const id=++this.timer;this.timers.set(id,callback);return id;},
  clearTimeout(id){this.timers.delete(id);},
};
const context={
  $: id =>{assert.equal(id,"clock-video");return clock;},
  state,
  pause:()=>{},
  seek:(time,force)=>{
    seeks.push({time,force});
    state.time=time;
    clock.currentTime=time;
  },
  videos:()=>[1,2],
  resumeSlave:video=>followerCalls.push(video),
  syncVideos:forced=>notes.push(["sync",forced]),
  updatePlayLabel:()=>{},
  performance:{now:()=>12_345},
  requestAnimationFrame:cb=>{ticks.push(cb);return ticks.length;},
  clockTick:()=>{},
  setTimeout:fn=>fakeTime.setTimeout(fn),
  clearTimeout:id=>fakeTime.clearTimeout(id),
  Promise,Math,Number,console,hook:{}
};
vm.runInNewContext(actual + "\nhook.play=play;hook.wait=waitForClockSeek;",
  context);
const {play,wait} = context.hook;
async function flush() {await Promise.resolve();await Promise.resolve();}
(async()=>{
  // Replay from EOF. The master clock must not play before seeked.
  const replay=play();
  assert.equal(seeks.length,1);
  assert.equal(seeks[0].time,0);
  assert.equal(clock.seeking,true);
  assert.equal(clock.playCalls.length,0);
  assert.equal(followerCalls.length,0);
  assert.equal(ticks.length,0);
  clock.emit("seeked");
  await replay;
  assert.deepEqual(clock.playCalls,[0]);
  assert.deepEqual(followerCalls,[1,2]);
  assert.equal(ticks.length,1);
  assert.equal(state.clockFailed,false);
  assert.equal(state.time,0);

  // Cancellation at EOF before seeked must not resurrect video playback.
  clock.pause();state.playing=false;state.time=18.05;state.duration=18.05;
  const p2=play();
  assert.equal(seeks.length,2);
  state.playing=false;state.playGeneration++;
  clock.emit("seeked");
  await p2;
  assert.equal(clock.playCalls.length,1,
    "canceled replay must not invoke a second play()");
  assert.equal(followerCalls.length,2);

  // Missing/unavailable clock can fall back to JS timeline; no deadlock.
  state.playing=false;state.time=5;clock.readyState=0;clock.seeking=false;
  const fallback=play();
  assert.equal(clock.playCalls.length,1);
  clock.emit("error");
  await fallback;
  assert.equal(state.clockFailed,true);
  assert.equal(ticks.length,2);
  assert.equal(followerCalls.length,4);
  assert.equal(clock.playCalls.length,1);

  // Stale master EOF after explicit reset to 0 must be ignored.
  const endedStart=source.indexOf('  $("clock-video").addEventListener("ended", () => {');
  const endedEnd=source.indexOf('  window.addEventListener("keydown"',endedStart);
  assert(endedStart>=0&&endedEnd>endedStart);
  let endedHandler=null;
  const dom={addEventListener:(name,cb)=>{if(name==="ended")endedHandler=cb;}};
  const eventContext={
    $:id=>{assert.equal(id,"clock-video");return dom;},
    state:{manifest:state.manifest,time:0,duration:18.05},
    seek:()=>{throw Error("stale EOF must not reset timeline")},
    pause:()=>{throw Error("stale EOF must not stop replay")},
    console,
  };
  vm.runInNewContext(source.slice(endedStart,endedEnd),eventContext);
  assert.equal(typeof endedHandler,"function");
  endedHandler();

  console.log("G2_REPLAY_MASTER_SEEK_AWAIT_CANCEL_AND_EOF_RACE_PASS");
})().catch(e=>{console.error(e);process.exitCode=1;});
