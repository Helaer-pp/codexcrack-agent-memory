// Exercise exported inline viewer code with a DOM/canvas stub; no browser layout claim.
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const html = fs.readFileSync(process.argv[2], 'utf8');
const source = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const noop = () => {};
const canvas = new Proxy({}, {get: (o,k) => o[k] ?? noop});
const elements = Object.fromEntries(['case','mode','x','plot','status','rows','prev','next'].map(id => [id, {value:'', getContext:()=>canvas}]));
elements.case.value = 'A'; elements.mode.value = 'joint';
const context = vm.createContext({document:{getElementById:id=>elements[id]}, Image: class {}, assert});
vm.runInContext(source, context);
const result = vm.runInContext(`(()=>{
 let columns=0, candidates=0;
 for (const name of 'ABCD') for (const mode of ['joint','current']) {
  c.value=name; m.value=mode; c.onchange();
  const v=DATA[name][mode], keys=Object.keys(v.columns);
  assert.equal(Number(x.value), Math.min(...keys.map(Number)));
  for(const key of keys) {
   x.value=key; x.onchange(); const col=v.columns[key];
   assert.equal(col.filter(r=>r.selected).length,1);
   assert.equal((document.getElementById('rows').innerHTML.match(/<tr /g)||[]).length,col.length);
   const chosen=col.find(r=>r.selected), t=v.trace.find(r=>r.x===Number(key));
   assert.equal(chosen.y,t.y); assert.equal(chosen.is_observed,t.observed);
   columns++; candidates+=col.length;
  }
  c.onchange(); const start=Number(x.value);
  document.getElementById('next').onclick(); assert.equal(Number(x.value),start+1);
  document.getElementById('prev').onclick(); assert.equal(Number(x.value),start);
  document.getElementById('prev').onclick(); assert.equal(Number(x.value),start);
  x.value='invalid'; x.onchange(); assert.equal(Number(x.value),start);
 }
 return {passed:true,columns,candidates,scope:'Inline JS and controls with DOM/canvas stub; PNGs visually inspected separately'};
})()`, context);
process.stdout.write(JSON.stringify(result,null,2));
