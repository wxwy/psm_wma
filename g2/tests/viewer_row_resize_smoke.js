"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
const source=fs.readFileSync(__dirname+"/../viewer/viewer.js","utf8");
const css=fs.readFileSync(__dirname+"/../viewer/viewer.css","utf8");
const html=fs.readFileSync(__dirname+"/../viewer/index.html","utf8");
const begin=source.indexOf("  function setRowHeight(row, shell, grid, pixels = null) {");
const end=source.indexOf("  async function initialize() {",begin);
assert(begin>0&&end>begin,"real row resize and layout functions must be used");
class El {
  constructor(tag){
    this.tag=tag;this.children=[];this.dataset={};this.attrs={};
    const properties=new Map();
    this.style={
      properties,setProperty:(k,v)=>properties.set(k,v),
      removeProperty:k=>properties.delete(k),
    };
    this.listeners={};this.className="";this.disabled=false;
    this._capture=null;this.textContent="";
  }
  append(...items){this.children.push(...items);}
  replaceChildren(...items){this.children=items;}
  setAttribute(key,value){this.attrs[key]=value;}
  addEventListener(name,callback){this.listeners[name]=callback;}
  setPointerCapture(pointerId){this._capture=pointerId;}
  hasPointerCapture(pointerId){return this._capture===pointerId;}
  releasePointerCapture(pointerId){if(this._capture===pointerId)this._capture=null;}
  getBoundingClientRect(){
    if(this.className==="display-row"){
      const stored=this.style.properties.get("--row-height");
      const height=stored?Number.parseFloat(stored):({
        1:340,2:360,3:380,4:285,5:250,
      })[this.children.length]||100;
      return {height};
    }
    return {height:100};
  }
  fire(name,extra={}){
    const cb=this.listeners[name];
    assert(cb,"Missing "+name+" on "+this.className);
    cb({
      button:0,pointerId:1,clientY:100,key:"",
      shiftKey:false,
      preventDefault(){this.defaultPrevented=true;},
      stopPropagation(){this.propagationStopped=true;},
      ...extra,
    });
  }
}
const container=new El("div");
const state={
  rows:[
    {id:"r1",blocks:["left","right","wrist"].map((source,i)=>
      ({id:"b"+i,source,displayMode:"contain"}))},
    {id:"r2",blocks:[{id:"other",source:"floor_top"}]},
  ],
  media:[],lastSpatial:-1,playing:false,drag:null,manifest:null,
  availableCameras:new Set(["left","right","wrist"]),
};
let saved=0,renders=0,nextId=0,storage="";
const context={
  state,
  $:id=>{assert.equal(id,"display-rows");return container;},
  document:{createElement:tag=>new El(tag)},
  newTile:block=>{const el=new El("article");el.dataset.block=block.id;return el;},
  updateTimeline:()=>{renders++;},
  videos:()=>[],
  saveLayout:()=>{saved++;storage=JSON.stringify(state.rows);},
  uuid:()=>String(++nextId),
  toast:()=>{},
  availableSources:()=>[{sources:[
    ["left"],["right"],["wrist"],["floor_top"],["plus_X"],["plus_Y"],
  ]}],
  clamp:(v,lo,hi)=>Math.min(hi,Math.max(lo,v)),
  validRowHeight:h=>Number.isInteger(h)&&h>=100&&h<=2400,
  ROW_MIN_HEIGHT:100,ROW_MAX_HEIGHT:2400,
  moveTile:()=>{},Number,Math,console,
};
vm.runInNewContext(source.slice(begin,end)+
  "\nrenderLayout();\n",context);
function rowInfo(i){
  const shell=container.children[i];
  assert.equal(shell.className,"row-shell");
  assert.equal(shell.children.length,3);
  const [grid,rail,handle]=shell.children;
  assert.equal(grid.className,"display-row");
  assert.equal(rail.className,"row-control-rail");
  assert.equal(handle.className,"row-resize-handle");
  assert.equal(handle.attrs["aria-label"],
    "拖动调整展示行高度，双击恢复自动高度");
  return {shell,grid,rail,handle};
}
let row=rowInfo(0);
let other=rowInfo(1);
assert.equal(state.rows[0].heightPx,undefined);
assert.equal(row.grid.style.properties.has("--row-height"),false);
assert.notEqual(row.shell.dataset.fixedHeight,"true");
assert.equal(row.grid.getBoundingClientRect().height,380);
assert.equal(other.grid.getBoundingClientRect().height,340);

// Existing behavior must stay auto when a block is added to an untouched row.
row.rail.children[1].fire("click");
row=rowInfo(0);
assert.equal(state.rows[0].blocks.length,4);
assert.equal(state.rows[0].heightPx,undefined);
assert.equal(row.grid.getBoundingClientRect().height,285,
  "adding blocks must continue to change AUTO row height");
assert.equal(saved,1);
let baselineRenders=renders;

// Drag from its current computed size: row 1 becomes fixed, row 2 unchanged.
row.handle.fire("pointerdown",{clientY:100,pointerId:9});
assert.equal(row.handle._capture,9);
row.handle.fire("pointermove",{clientY:227,pointerId:9});
assert.equal(state.rows[0].heightPx,412);
assert.equal(row.grid.style.properties.get("--row-height"),"412px");
assert.equal(row.shell.dataset.fixedHeight,"true");
assert.equal(renders,baselineRenders,
  "pointermove must NOT rerender/cancel media playback");
assert.equal(saved,1,
  "do not write localStorage repeatedly during each pointer move");
assert.equal(other.grid.getBoundingClientRect().height,340,
  "dragging row 1 must not alter row 2");
row.handle.fire("pointerup",{clientY:227,pointerId:9});
assert.equal(saved,2);
assert.equal(row.handle._capture,null);
assert.equal(JSON.parse(storage)[0].heightPx,412);

// Adding a fifth block after a manual resize must keep the chosen 412px.
row.rail.children[1].fire("click");
row=rowInfo(0);
assert.equal(state.rows[0].blocks.length,5);
assert.equal(state.rows[0].heightPx,412);
assert.equal(row.grid.getBoundingClientRect().height,412);
assert.equal(row.shell.dataset.fixedHeight,"true");
assert.equal(saved,3);

// Cancelling an unfinished drag restores the previous explicit height.
row.handle.fire("pointerdown",{clientY:200,pointerId:10});
row.handle.fire("pointermove",{clientY:260,pointerId:10});
assert.equal(state.rows[0].heightPx,472);
row.handle.fire("pointercancel",{clientY:260,pointerId:10});
assert.equal(state.rows[0].heightPx,412);
assert.equal(saved,3,"cancelled resize does not persist");

// Double click returns row to natural size, now based on five columns.
row.handle.fire("dblclick");
assert.equal(state.rows[0].heightPx,undefined);
assert.equal(row.grid.style.properties.has("--row-height"),false);
assert.equal(row.shell.dataset.fixedHeight,"false");
assert.equal(row.grid.getBoundingClientRect().height,250);
assert.equal(saved,4);

// Keyboard support, with Home restoring natural sizing.
row.handle.fire("keydown",{key:"ArrowDown"});
assert.equal(state.rows[0].heightPx,260);
row.handle.fire("keydown",{key:"ArrowUp",shiftKey:true});
assert.equal(state.rows[0].heightPx,220);
row.handle.fire("keydown",{key:"Home"});
assert.equal(state.rows[0].heightPx,undefined);

// Minimum 100px and maximum 2400px are enforced.
row.handle.fire("pointerdown",{clientY:100,pointerId:11});
row.handle.fire("pointermove",{clientY:-999,pointerId:11});
assert.equal(state.rows[0].heightPx,100);
row.handle.fire("pointermove",{clientY:99999,pointerId:11});
assert.equal(state.rows[0].heightPx,2400);
row.handle.fire("pointerup",{clientY:99999,pointerId:11});

// Existing row remains independent, then its own drag can be applied.
other=rowInfo(1);
assert.equal(state.rows[1].heightPx,undefined);
other.handle.fire("pointerdown",{clientY:100,pointerId:12});
other.handle.fire("pointermove",{clientY:135,pointerId:12});
other.handle.fire("pointerup",{clientY:135,pointerId:12});
assert.equal(state.rows[1].heightPx,375);
assert.equal(state.rows[0].heightPx,2400);

// Validate the actual saved-layout parser, including backwards compatibility.
const validatorStart=source.indexOf("  const ROW_MIN_HEIGHT = 100;");
const validatorEnd=source.indexOf("  function isLegacyDefault(rows) {",validatorStart);
assert(validatorStart>0&&validatorEnd>validatorStart);
const validationHooks={};
vm.runInNewContext(source.slice(validatorStart,validatorEnd)+
  "\nvalidationHooks.check=validSavedLayout;\n",{
    validationHooks,
    validSource:s=>typeof s==="string",
    VALID_DISPLAY_MODES:new Set(["native","height","width","contain"]),
    Number,Set,Array,
  });
const isValid=validationHooks.check;
assert(isValid(state.rows),"both manually resized rows must validate");
assert(isValid([{id:"old",blocks:[{id:"oldb",source:"left"}]}]),
  "old rows without explicit height must still validate");
for(const invalidHeight of [0,99,2401,-100,NaN,Infinity,"400",200.5]){
  const candidate=JSON.parse(JSON.stringify(state.rows));
  candidate[0].heightPx=invalidHeight;
  assert(!isValid(candidate),"invalid saved row height: "+invalidHeight);
}
assert(!html.includes('class="workspace-head"'));
assert(css.includes('.row-resize-handle {'));
assert(css.includes('touch-action:none;user-select:none'));
assert(css.includes('.row-shell[data-fixed-height="true"] .display-row'));
assert(css.includes('height:var(--row-height)'));
assert(css.includes('.row-shell[data-fixed-height="true"] .tile-visual'));
assert(css.includes('aspect-ratio:auto'));
assert(html.includes("viewer.js?v=20261116-row-height"));
assert(html.includes("viewer.css?v=20261116-row-height"));
console.log("G2_ROW_DRAG_HEIGHT_AUTO_FIXED_PERSIST_ADD_RESET_PASS");
