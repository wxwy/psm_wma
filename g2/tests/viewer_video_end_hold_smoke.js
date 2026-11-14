"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source = fs.readFileSync(__dirname + "/../viewer/viewer.js","utf8");
const begin = source.indexOf("  const MEDIA_TAIL_MARGIN = ");
const end = source.indexOf("  function seek(time, force = false) {",begin);
assert(begin>=0&&end>begin);
const endedStart=source.indexOf('      video.addEventListener("ended", () => {');
const endedEnd=source.indexOf('      video.addEventListener("error",',endedStart);
assert(endedStart>0&&endedEnd>endedStart);
const actualEndedHandler=source.slice(endedStart,endedEnd);
assert(actualEndedHandler.includes("parkFollowerAtEnd(video)"));
assert(!actualEndedHandler.includes("resumeSlave(video)"));

class Media {
  constructor(name,duration=12) {
    this.name=name;this.duration=duration;this.readyState=1;
    this.playbackRate=1;this.paused=false;this.ended=false;
    this.seeking=false;this._currentTime=11.8;
    this.listeners={};this.calls=[];
  }
  get currentTime(){return this._currentTime;}
  set currentTime(value){
    this.calls.push(["seek",value]);
    this._currentTime=value;
    this.seeking=true;
    // Browser can keep ended=true until the seek has actually settled.
  }
  pause(){this.paused=true;this.calls.push(["pause"]);}
  play(){
    if(this.ended){
      this._currentTime=0;
      this.calls.push(["UNWANTED_AUTOREWIND"]);
    }
    this.paused=false;
    this.calls.push(["play",this._currentTime]);
    return Promise.resolve();
  }
  addEventListener(name,callback,options){
    (this.listeners[name]??=[]).push({callback,once:options?.once});
  }
  emit(name){
    if(name==="seeked"){this.seeking=false;this.ended=false;}
    for(const listener of [...(this.listeners[name]||[])]) listener.callback();
    this.listeners[name]=(this.listeners[name]||[]).filter(x=>!x.once);
  }
}
const clock=new Media("clock");
const right=new Media("right"), wrist=new Media("wrist");
const state={playing:true,manifest:{states:[{frame:0}]},
  time:11.8,speed:1,media:[
  {video:right,disposed:false},{video:wrist,disposed:false}
]};
const context={
 state,video:null,tile:null,hook:{},
 $:id=>{assert.equal(id,"clock-video");return clock;},
 videos:()=>[right,wrist],
 WeakSet,Number,Math,Error,Promise,console,
 clamp:(x,lo,hi)=>Math.max(lo,Math.min(x,hi)),
};
vm.runInNewContext(source.slice(begin,end)+
  "\nhook.resume=resumeSlave;hook.sync=syncVideos;"+
  "\nhook.park=parkFollowerAtEnd;"+
  "\nhook.release=releaseFollowerHoldsOnRewind;",context);
for(const [video,tile] of [[right,state.media[0]],[wrist,state.media[1]]]){
  // Capture each video's identity as lexical parameters, just as newTile
  // does; do not reference a mutable VM-global "video" variable.
  vm.runInNewContext("(function(video,tile){"+actualEndedHandler+"})",
    context)(video,tile);
}
function assertStillLast(video){
 assert(video.currentTime>video.duration-0.05,
   video.name+" must show last MP4 frame, not first");
 assert(video.paused,video.name+" must remain paused at EOF");
 assert(!video.calls.some(c=>c[0]==="UNWANTED_AUTOREWIND"));
}
function playCount(video){return video.calls.filter(c=>c[0]==="play").length;}
function seekCount(video){return video.calls.filter(c=>c[0]==="seek").length;}

// A follower can finish before the Left master clock (browser lag/jitter).
for(const video of [right,wrist]){
  video.ended=true;video._currentTime=12;
  video.emit("ended");
  assertStillLast(video);
  assert(video.seeking);
  assert.equal(seekCount(video),1,"only one terminal-frame seek");
  const p=playCount(video);
  // Reentrant EOF notification and periodic clock alignment cannot re-seek
  // during pending seek or restart a camera while master is 200ms behind.
  video.emit("ended");
  context.hook.sync();
  context.hook.resume(video);
  assert.equal(seekCount(video),1,"do not restart pending terminal seek");
  assert.equal(playCount(video),p,"finished follower must never replay");
  video.emit("seeked");
  context.hook.resume(video);
  assertStillLast(video);
  assert.equal(playCount(video),p);
}
// Main timeline approaches the end, even though it was previously behind.
for(const t of [11.84,11.9,11.96,12]){
  state.time=t;
  context.hook.sync(false);
  for(const video of [right,wrist]){
    context.hook.resume(video);
    assertStillLast(video);
    assert.equal(playCount(video),0);
  }
}

// Browser has not yet emitted ended but follower enters the last two frames;
// proactively freeze its last image before it could hit browser EOF.
right._currentTime=11.85;right.ended=false;right.seeking=false;right.paused=false;
state.time=11.93;
context.hook.sync(false);
assertStillLast(right);

// Explicit rewind to 4.0s resets the EOF latch, preserving user seeking.
state.time=4;
context.hook.release(12,4);
context.hook.sync(true);
for(const video of [right,wrist]){
 assert.equal(video.currentTime,4);
 assert(video.seeking);
 video.emit("seeked");
 context.hook.resume(video);
 assert.equal(video.currentTime,4);
 assert.equal(playCount(video),1);
 assert(!video.calls.some(c=>c[0]==="UNWANTED_AUTOREWIND"));
}
console.log("G2_REAL_ENDED_EVENT_LAST_FRAME_HOLD_RIGHT_WRIST_PASS");