"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
const source=fs.readFileSync(__dirname+"/../viewer/viewer.js","utf8");
const begin=source.indexOf("  function setRowHeight(row, shell, grid, pixels = null) {");
const end=source.indexOf("  async function initialize() {",begin);
assert(begin>=0&&end>begin);
const fragment=source.slice(begin,end);
class El {
  constructor(tag){
    this.tag=tag;this.children=[];this.dataset={};this.attrs={};
    const properties=new Map();
    this.style={properties,
      setProperty:(k,v)=>properties.set(k,v),
      removeProperty:(k)=>properties.delete(k)};
    this.listeners={};this.textContent="";this.className="";this.disabled=false;
  }
  append(...children){this.children.push(...children);}
  replaceChildren(...children){this.children=children;}
  setAttribute(k,v){this.attrs[k]=v;}
  addEventListener(event,callback){this.listeners[event]=callback;}
  click(){assert(this.listeners.click,this.className);this.listeners.click();}
}
const container=new El("div");
const makeRow=(id,viewIds)=>({
  id,blocks:viewIds.map((source,i)=>({id:id+"-block-"+i,source}))
});
const state={
  rows:[makeRow("row-a",["floor_top","left","right"]),
    makeRow("row-b",["plus_Y"])],
  media:[],lastSpatial:-1,playing:false,drag:null,manifest:null,
  availableCameras:new Set(["left","right","wrist"])
};
let rerenders=0,serial=0;
const scope={
  state,
  $:id=>{assert.equal(id,"display-rows");return container;},
  document:{createElement:tag=>new El(tag)},
  newTile:block=>{const el=new El("article");el.dataset.block=block.id;return el;},
  updateTimeline:()=>{rerenders++;},
  videos:()=>[],
  saveLayout:()=>{},
  uuid:()=>String(++serial),
  toast:()=>{},
  SOURCES:[],
  availableSources:()=>[
    {sources:[["floor_top"],["left"],["right"],["wrist"],["plus_X"],["plus_Y"]]}
  ],
  clamp:(v,lo,hi)=>Math.max(lo,Math.min(v,hi)),
  validRowHeight:v=>Number.isInteger(v)&&v>=100&&v<=2400,
  ROW_MIN_HEIGHT:100,ROW_MAX_HEIGHT:2400,
  moveTile:()=>{},
  console,
};
vm.runInNewContext(fragment+"\nrenderLayout();",scope);
assert.equal(container.children.length,2);
function inspectRow(n){
 const shell=container.children[n];
 assert.equal(shell.className,"row-shell");
 assert.equal(shell.children.length,3,
   "row grid, floating actions and resize grip are the only shell children");
 const [grid,rail,resize]=shell.children;
 assert.equal(resize.className,"row-resize-handle");
 assert.equal(resize.title,"上下拖动调整行高 · 双击恢复自动高度");
 assert.equal(grid.className,"display-row");
 assert.equal(rail.className,"row-control-rail");
 assert.equal(rail.attrs.role,"group");
 assert.equal(grid.children.length,state.rows[n].blocks.length);
 assert.equal(rail.children.length,2);
 const [del,add]=rail.children;
 assert.equal(del.className,"remove-row");
 assert.equal(del.textContent,"✕");
 assert.equal(del.title,"删除整行");
 assert.equal(del.attrs["aria-label"],"删除整行");
 assert.equal(add.className,"add-block");
 assert.equal(add.textContent,"+");
 assert.equal(add.title,"添加显示块");
 assert.equal(add.attrs["aria-label"],"添加显示块");
 return {grid,rail,del,add,resize};
}
let {add}=inspectRow(0);
inspectRow(1);
add.click();
assert.equal(state.rows[0].blocks.length,4);
assert.equal(container.children.length,2);
({add}=inspectRow(0));
add.click();
assert.equal(state.rows[0].blocks.length,5);
({add}=inspectRow(0));
assert.equal(add.disabled,true,"five blocks is the maximum");
const removeSecond=inspectRow(1).del;
removeSecond.click();
assert.equal(state.rows.length,1);
assert.equal(container.children.length,1);
assert.equal(inspectRow(0).del.disabled,true,"cannot remove last row");
assert(rerenders>=4);
console.log("G2_ABSOLUTE_ROW_CONTROL_RAIL_ADD_REMOVE_AND_MAX_FIVE_PASS");