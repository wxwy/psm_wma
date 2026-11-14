"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source = fs.readFileSync(__dirname + "/../viewer/viewer.js","utf8");
const start = source.indexOf("  const MEDIA_TAIL_MARGIN = ");
const end = source.indexOf("  function seek(time, force = false) {", start);
assert(start >= 0 && end > start, "sync functions found");

class Media {
  constructor(name, duration=12) {
    this.name=name;
    this.duration=duration;
    this.readyState=1;
    this.playbackRate=1;
    this.paused=true;
    this.ended=false;
    this.seeking=false;
    this._currentTime=0;
    this.calls=[];
    this.listeners={};
  }
  get currentTime() {return this._currentTime;}
  set currentTime(value) {
    this.calls.push(["seek",value]);
    this._currentTime=value;
    this.seeking=true;
    this.ended=false;
  }
  pause() {this.paused=true;this.calls.push(["pause"]);}
  play() {
    if(this.ended) {
      // This is precisely the browser behavior to prevent: restarting an
      // ended follower from timestamp 0 on play().
      this._currentTime=0;
      this.calls.push(["REWOUND_TO_ZERO"]);
    }
    this.paused=false;
    this.calls.push(["play",this._currentTime]);
    return Promise.resolve();
  }
  addEventListener(name,callback,options) {
    (this.listeners[name] ||= []).push({callback,once:options?.once});
  }
  emit(name) {
    if(name==="seeked") this.seeking=false;
    const list=this.listeners[name]||[];
    this.listeners[name]=list.filter(item=>!item.once);
    for(const item of list)item.callback();
  }
}

const left=new Media("clock");
const right=new Media("right");
const wrist=new Media("wrist");
const state={
  playing:true,manifest:{states:[{frame:0}]},
  time:7.5,speed:1,media:[
    {video:right,disposed:false},{video:wrist,disposed:false}
  ],
};
const hooks={};
const context={state,hooks,
  $:id=>{assert.equal(id,"clock-video");return left;},
  videos:()=>[right,wrist],
  WeakSet,Number,Math,Error,Promise,console,
  clamp:(v,min,max)=>Math.min(max,Math.max(min,v))};
vm.runInNewContext(source.slice(start,end)+
  "\nhooks.resume=resumeSlave;hooks.sync=syncVideos;" +
  "\nhooks.mediaAtEnd=mediaAtEnd;hooks.align=alignMedia;\n",context);
const {resume,sync}=hooks;

function approx(actual,expected,eps=0.025) {
  assert(Math.abs(actual-expected)<=eps,actual+" != "+expected);
}
(async()=>{
  sync(true);
  approx(right.currentTime,7.5);
  approx(wrist.currentTime,7.5);
  assert(right.seeking&&wrist.seeking);
  resume(right);resume(right);resume(wrist);
  assert(!right.calls.some(c=>c[0]==="play"),"must not play during seek");
  assert.equal(right.listeners.seeked.length,1,"no duplicate seeked listeners");
  right.emit("seeked"); wrist.emit("seeked");
  assert(!right.paused&&!wrist.paused);
  assert.equal(right.calls.find(c=>c[0]==="play")[1],7.5);
  assert.equal(wrist.calls.find(c=>c[0]==="play")[1],7.5);

  // Paused and resumed at a nonzero timeline, never from the start.
  right.pause();wrist.pause();state.playing=false;state.time=9.05;
  sync(true);
  assert(right.seeking&&wrist.seeking);
  state.playing=true;
  resume(right);resume(wrist);
  right.emit("seeked");wrist.emit("seeked");
  approx(right.calls.at(-1)[1],9.05);
  approx(wrist.calls.at(-1)[1],9.05);
  assert(!right.calls.some(c=>c[0]==="REWOUND_TO_ZERO"));

  // An independent video reaches EOF ahead of the master. Do not call
  // its play() again while the common timeline is already at the tail.
  state.time=12;
  right.paused=true;right.ended=true;right.seeking=false;
  right._currentTime=12;
  const plays=right.calls.filter(c=>c[0]==="play").length;
  resume(right);
  assert.equal(right.calls.filter(c=>c[0]==="play").length,plays);
  assert.equal(right.currentTime,11.975);
  assert(!right.calls.some(c=>c[0]==="REWOUND_TO_ZERO"));

  // If a follower ended early, seeking to the master time must finish
  // before play is permitted, so it never auto-rewinds to zero.
  state.time=4.5;
  right.ended=true;right.paused=true;right.seeking=false;
  right._currentTime=12;
  resume(right);
  assert(right.seeking);
  approx(right.currentTime,4.5);
  const playsBefore=right.calls.filter(c=>c[0]==="play").length;
  assert.equal(right.calls.filter(c=>c[0]==="play").length,playsBefore);
  right.emit("seeked");
  assert.equal(right.calls.filter(c=>c[0]==="play").length,playsBefore+1);
  assert(!right.calls.some(c=>c[0]==="REWOUND_TO_ZERO"));

  // Recreated stale tiles must never restart or continue playing.
  state.media[0].disposed=true;
  right.pause();
  const previous=right.calls.length;
  resume(right);
  assert.equal(right.calls.length,previous);
  console.log("G2_RIGHT_WRIST_MASTER_TIMELINE_NO_AUTO_REWIND_PASS");
})().catch(e=>{console.error(e);process.exitCode=1;});