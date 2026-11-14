"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const script = fs.readFileSync(__dirname + "/../viewer/viewer.js", "utf8");
const css = fs.readFileSync(__dirname + "/../viewer/viewer.css", "utf8");
const html = fs.readFileSync(__dirname + "/../viewer/index.html", "utf8");

class El {
  constructor(name) {
    this.tagName = name.toUpperCase();
    this.children = [];
    this.listeners = {};
    this.dataset = {};
    this.attrs = {};
    this.style = {};
    this.className = "";
    this.hidden = false;
    this.disabled = false;
    this.value = "";
    this.textContent = "";
    this.offsetTop = 0;
    this.offsetHeight = 27;
    this.clientHeight = 150;
    this.scrollHeight = 150;
  }
  get options() {
    if(this.tagName!=="SELECT") return undefined;
    const out=[];
    const walk=node=>{
      for(const child of node.children) {
        if(child.tagName==="OPTION")out.push(child);
        else walk(child);
      }
    };
    walk(this);
    return out;
  }
  append(...nodes) {for(const n of nodes){n.parentElement=this;this.children.push(n);}}
  prepend(...nodes) {for(const n of [...nodes].reverse()){n.parentElement=this;this.children.unshift(n);}}
  replaceChildren(...nodes) {this.children=[];this.append(...nodes);}
  setAttribute(key,value){this.attrs[key]=value;}
  getAttribute(key){return this.attrs[key];}
  addEventListener(key,fn){(this.listeners[key] ||= []).push(fn);}
  removeEventListener(key,fn){this.listeners[key]=(this.listeners[key]||[]).filter(x=>x!==fn);}
  focus(){this.focused=true;}
  remove(){this.parentElement?.children.splice(this.parentElement.children.indexOf(this),1);}
  contains(other){return other===this||this.children.some(n=>n.contains(other));}
  getBoundingClientRect(){return {left:20,top:30,right:200,bottom:50,width:180,height:20};}
  querySelectorAll(selector){
    if(selector===".g2-select-option:not(:disabled)")
      return this.children.filter(x=>x.className==="g2-select-option" && !x.disabled);
    return [];
  }
  dispatchEvent(event){
    for(const listener of this.listeners[event.type]||[]) listener(event);
  }
  fire(type,event={}){
    this.dispatchEvent({type,button:0,key:"",altKey:false,
      preventDefault(){this.defaultPrevented=true;},
      stopPropagation(){},target:this,...event});
  }
}

const state = {
  manifest:null,media:[],rows:[],playing:false,drag:null,
  availableCameras:new Set(["left","right","wrist"])
};
const document={body:new El("body"),events:{},
  createElement:name=>new El(name),
  addEventListener(key,fn){this.events[key]=fn;},
  removeEventListener(key){delete this.events[key];},
  querySelectorAll:()=>[],
  activeElement:null};
const window={innerWidth:1200,innerHeight:800,events:{},
  addEventListener(key,fn){this.events[key]=fn;},
  removeEventListener(key){delete this.events[key];}};
const hooks={};
let saved=0,rendered=0,styleEnhancements=0;
const context = {
  document,window,state,hooks,console,
  Event:class Event {constructor(type){this.type=type;}},
  WeakSet,Set,Map,Math,Number,Promise,
  sourceMetadata:()=>["floor_top","俯视","2Hz"],
  fillSourceSelect:(el,selected)=>{
    el.value=selected;
    const option=new El("option");option.value=selected;option.textContent=selected;
    el.append(option);
    return selected;
  },
  parseIslandSource:()=>null,
  validSource:()=>true,
  VIDEO:new Set(["left","right","wrist"]),
  DISPLAY_MODES:[["native","原尺寸"],["height","高对齐"],
    ["width","宽对齐"],["contain","自适应"]],
  VALID_DISPLAY_MODES:new Set(["native","height","width","contain"]),
  displayMode:block=>
    ["native","height","width","contain"].includes(block.displayMode)?
      block.displayMode:"contain",
  saveLayout:()=>{saved++;},
  renderLayout:()=>{rendered++;},
  clearDrag:()=>{},
  requestAnimationFrame:()=>{},
  videoUrl:()=>"none.mp4",
  resumeSlave:()=>{},
  alignMedia:()=>{},
};
const begin = script.indexOf("  let activeStyledMenu = null;");
const end = script.indexOf("  function clearDrag() {", begin);
assert(begin>=0&&end>begin);
vm.runInNewContext(script.slice(begin,end)+
  "\nhooks.newTile=newTile;hooks.enable=enableStyledSelect;"+
  "\nhooks.open=showStyledSelectMenu;hooks.close=closeStyledSelectMenu;\n",
  context);

const block={id:"b1",source:"floor_top"};
const row={id:"r1",blocks:[block]};
const card=hooks.newTile(block,row,0);
assert.equal(card.className,"tile");
const toolbar=card.children[0];
const visual=card.children[1];
assert.equal(toolbar.children.length,4);
const [handle,sourceSelect,modeSelect,remove]=toolbar.children;
assert.equal(modeSelect.className,"tile-fit-select");
assert.equal(modeSelect.children.length,4);
assert.equal(modeSelect.value,"contain","old stored block defaults to containment");
assert.equal(visual.dataset.displayMode,"contain");
assert.equal(state.media.length,1);
const canvas=state.media[0].canvas;
assert(canvas && canvas.className==="tile-media");
for(const mode of ["height","width","native","contain"]){
  modeSelect.value=mode;
  modeSelect.fire("change");
  assert.equal(block.displayMode,mode);
  assert.equal(visual.dataset.displayMode,mode);
  assert.equal(state.media[0].canvas,canvas,"must not replace media on fit changes");
}
assert.equal(rendered,0,"fitting changes must not rebuild view tiles");
assert.equal(saved,4);

// The actual menu highlight is tied ONLY to the committed selected value.
modeSelect.value="height";
hooks.open(modeSelect);
let menu=document.body.children.at(-1);
assert.equal(menu.className,"g2-select-menu");
const options=menu.children.filter(x=>x.className==="g2-select-option");
assert.equal(options.length,4);
assert.equal(options.filter(x=>x.attrs["aria-selected"]==="true").length,1);
assert.equal(options[1].attrs["aria-selected"],"true");
assert.equal(options[0].attrs["aria-selected"],"false");
assert(options.every(x=>x.attrs.role==="option"));
assert(menu.attrs.role==="listbox");
assert.equal(modeSelect.attrs["aria-expanded"],"true");

// Hover is purely CSS; choosing an option changes native select value and
// fires the original change handler, preserving the source of truth.
options[2].fire("click");
assert.equal(modeSelect.value,"width");
assert.equal(block.displayMode,"width");
assert.equal(visual.dataset.displayMode,"width");
assert.equal(modeSelect.attrs["aria-expanded"],"false");
assert.equal(document.body.children.length,0);
assert.equal(saved,5);
assert.equal(rendered,0);

// Source menu is also enhanced; these controls retain their existing
// native change behavior and do not alter the other per-tile mode.
assert(sourceSelect.listeners.pointerdown?.length===1);
assert(modeSelect.listeners.pointerdown?.length===1);
const event={button:0,preventDefault(){this.defaultPrevented=true;}};
modeSelect.fire("pointerdown",event);
assert.equal(document.body.children.length,1);
modeSelect.fire("pointerdown",event);
assert.equal(document.body.children.length,0,"second click toggles menu off");
modeSelect.disabled=true;modeSelect.fire("pointerdown",event);
assert.equal(document.body.children.length,0,"disabled dropdown never opens");

const beforeCSS = [
  '.g2-select-option:not([aria-selected="true"]):hover',
  '.g2-select-option[aria-selected="true"]',
  '.g2-select-option[aria-selected="true"]:hover',
  'background:#f1f3f6',
  'background:#4265dd;color:#fff',
];
for(const item of beforeCSS)assert(css.includes(item),item);
assert(css.includes('.tile-visual[data-display-mode="native"] .tile-media'));
assert(css.includes('.tile-visual[data-display-mode="height"] .tile-media'));
assert(css.includes('.tile-visual[data-display-mode="width"] .tile-media'));
assert(css.includes('.tile-visual[data-display-mode="contain"] .tile-media'));
assert(html.includes('viewer.js?v=20261114-display-mode-menu'));
console.log("G2_PER_TILE_DISPLAY_MODE_CHANGE_PRESERVES_MEDIA_PASS");
