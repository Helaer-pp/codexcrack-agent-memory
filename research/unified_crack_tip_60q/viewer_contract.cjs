// Small DOM contract smoke, no network/browser dependency; not a browser screenshot test.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const run=process.argv[2];
class Element{
  constructor(id=''){this.id=id;this.value=id==='frames'?'0':'';this.style={};this.children=[];this.selectedIndex=0;this._html='';}
  append(...v){this.children.push(...v)} remove(){}
  set innerHTML(v){this._html=v;this.children=[]}get innerHTML(){return this._html}
}
const nodes={};const context={document:{getElementById:id=>nodes[id]||(nodes[id]=new Element(id)),createElement:()=>new Element(),body:new Element()},console};context.window=context;
vm.createContext(context);vm.runInContext(fs.readFileSync(run+'/qa/viewer_script.js','utf8'),context);
vm.runInContext(fs.readFileSync(run+'/galleries/frames/group_a/1/data.js','utf8'),context);
assert(nodes.title.textContent.includes('BUDGET_EXHAUSTED'));assert(nodes.candidates.textContent.includes('rejected_reasons'));
assert(nodes.links.innerHTML.includes('../raw_inference/FULL/group_a/1.json.gz'));assert.equal(nodes.layers.children.length,8);
assert(JSON.parse(nodes.candidates.textContent).length<=50);const firstCandidate=JSON.parse(nodes.candidates.textContent)[0].id;context.candidatePageMove(1);assert.notEqual(JSON.parse(nodes.candidates.textContent)[0].id,firstCandidate);
nodes.candidateQuery.value='0';context.candidateTable();assert(JSON.parse(nodes.candidates.textContent).length<=1);
nodes.extra.value='jump';context.filter();assert.equal(nodes.frames.children.length,0);assert.equal(context.window.frameData,null);assert.equal(nodes.stage.children.length,0);
nodes.extra.value='budget';context.filter();assert.equal(nodes.frames.children.length,1);
nodes.extra.value='preferred';context.filter();assert.equal(nodes.frames.children.length,1);
console.log('Viewer JS syntax / frame loading / 8 layer toggles / candidate filter / budget-jump filter contracts PASS; no claim of real-browser automation.');
