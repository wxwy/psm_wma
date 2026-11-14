"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source = fs.readFileSync(__dirname + "/../viewer/viewer.js", "utf8");
const html = fs.readFileSync(__dirname + "/../viewer/index.html", "utf8");
const css = fs.readFileSync(__dirname + "/../viewer/viewer.css", "utf8");

const start = source.indexOf("  const TIMELINE_MORPH_DISTANCE = ");
const stop = source.indexOf('  $("clock-video").addEventListener("loadedmetadata"',start);
assert(start >= 0 && stop > start);
const code = source.slice(start,stop);

function element() {
  return {
    disabled:false, inert:false, dataset:{},
    style:{
      properties:new Map(),
      setProperty(key,value) {this.properties.set(key,value);},
    },
  };
}
const anchor=element();
anchor.top=50;
anchor.getBoundingClientRect=()=>({top:anchor.top});
const panel=element(), bottom=element();
const buttons={
  "compact-prev":element(),
  "compact-play":element(),
  "compact-next":element(),
};
const els={"timeline-scroll-anchor":anchor,"timeline-panel":panel,
  "player-bottom":bottom,...buttons};
const events={};
const frames=[];
let narrow=false;
const win={
  matchMedia:()=>({matches:narrow}),
  addEventListener(type, callback) {events[type]=callback;},
};
const state={manifest:{states:[{frame:0}]},timelineMorph:0};
const hooks={};
vm.runInNewContext(
  code+"\nhooks.progress=timelineMorphProgress;"+
  "\nhooks.geometry=timelineMorphGeometry;"+
  "\nhooks.update=updateTimelineMorph;"+
  "\nhooks.schedule=scheduleTimelineMorph;",
  {
    state, hooks, window:win,
    $:id=>{assert(els[id],id);return els[id];},
    clamp:(v,min,max)=>Math.min(max,Math.max(min,v)),
    requestAnimationFrame:cb=>{frames.push(cb);return frames.length;},
    Map,Math,Object,console,
  }
);
assert.equal(typeof events.scroll,"function");
assert.equal(typeof events.resize,"function");
const {progress,geometry,update,schedule}=hooks;
assert.equal(progress(200),0);
assert.equal(progress(0),0);
assert.equal(progress(-76),0.5);
assert.equal(progress(-152),1);
assert.equal(progress(-330),1);
assert.deepEqual(Object.keys(geometry(0)),Object.keys(geometry(1)));

function property(name){return panel.style.properties.get(name);}
function allDisabled(expected){
  for(const button of Object.values(buttons)) assert.equal(button.disabled,expected);
}
update();
assert.equal(state.timelineMorph,0);
assert.equal(panel.dataset.compact,"false");
assert.equal(property("--timeline-header-height"),"56px");
assert.equal(property("--timeline-bottom-height"),"44px");
assert.equal(property("--timeline-controls-width"),"0px");
assert.equal(property("--timeline-compact-opacity"),"0");
assert.equal(property("--timeline-instruction-height"),"0px");
allDisabled(true);
assert.equal(bottom.inert,false);

anchor.top=-76;
events.scroll();events.scroll();events.scroll();
assert.equal(frames.length,1,"scroll must be requestAnimationFrame-throttled");
frames.shift()();
assert.equal(state.timelineMorph,0.5);
assert.equal(property("--timeline-original-opacity"),"0.5");
assert.equal(property("--timeline-compact-opacity"),"0.5");
assert.equal(property("--timeline-controls-width"),"52px");
assert.equal(panel.dataset.sticky,"true");
allDisabled(true); // controls fully usable only after mostly compact

anchor.top=-152;
events.scroll();frames.shift()();
assert.equal(state.timelineMorph,1);
assert.equal(property("--timeline-header-height"),"0px");
assert.equal(property("--timeline-bottom-height"),"0px");
assert.equal(property("--timeline-row-height"),"35px");
assert.equal(property("--timeline-instruction-height"),"31px");
assert.equal(property("--timeline-controls-width"),"104px");
assert.equal(property("--timeline-metrics-width"),"270px");
assert.equal(panel.dataset.compact,"true");
assert.equal(bottom.inert,true);
allDisabled(false);

state.manifest=null;
update();
allDisabled(true);
state.manifest={states:[{frame:0}]};

// Scroll up: compact timeline must reverse without the browser being reloaded.
anchor.top=-76;events.scroll();frames.shift()();
assert.equal(state.timelineMorph,0.5);
assert.equal(panel.dataset.compact,"false");
assert.equal(bottom.inert,false);
anchor.top=80;events.scroll();frames.shift()();
assert.equal(property("--timeline-compact-opacity"),"0");
assert.equal(property("--timeline-original-opacity"),"1");
assert.equal(panel.dataset.sticky,"false");

narrow=true;anchor.top=-152;events.resize();frames.shift()();
assert.equal(property("--timeline-controls-width"),"80px");
assert.equal(property("--timeline-metrics-width"),"128px");
assert.equal(property("--timeline-instruction-height"),"27px");

// DOM: exactly one original scrub, compact actions are not duplicated slider.
// Order of layout controls is after every row, not above the workspace.
const row=html.indexOf('id="display-rows"');
const actions=html.indexOf('class="workspace-actions"');
assert(row >= 0 && actions > row);
assert(!html.includes('class="workspace-head"'));
assert(!html.includes('class="workspace-end"'));
assert(html.indexOf('id="timeline-scroll-anchor"') <
  html.indexOf('id="timeline-panel"'));
assert(html.indexOf('id="sticky-instruction"') <
  html.indexOf('id="scrub"'));
assert.equal((html.match(/id="player-bottom"/g)||[]).length,1);
assert(html.includes('id="compact-prev"') &&
  html.includes('id="compact-play"') &&
  html.includes('id="compact-next"'));
assert.equal((html.match(/id="scrub"/g)||[]).length,1);
assert(source.includes('$("compact-prev").addEventListener("click", () => step(-1))'));
assert(source.includes('$("compact-play").addEventListener("click", play)'));
assert(source.includes('$("compact-next").addEventListener("click", () => step(1))'));
assert(source.includes('$("sticky-instruction").textContent'));
assert(source.includes('$("compact-frame-label").textContent'));
assert(source.includes('$("compact-source-frame-label").textContent'));
assert(source.includes('$("compact-time-current").textContent'));
assert(source.includes('shell.append(grid, rail);'));
assert(source.includes('remove.title = "删除整行"'));
assert(source.includes('add.title = "添加显示块"'));
assert(!source.includes('shell.append(head, grid)'));
assert(css.includes('position:sticky; top:0; z-index:30'));
assert(css.includes('position:absolute; top:0; bottom:0; right:-36px'));
assert(css.includes('.row-control-rail:hover'));
assert(css.includes('opacity:.22'));
console.log("G2_STICKY_TIMELINE_SCROLL_REVERSE_AND_FLOATING_ROW_CONTROLS_PASS");