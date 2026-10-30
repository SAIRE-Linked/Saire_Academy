/** Fast offline content and syntax smoke test. Full UI build also requires npm install. */
const fs=require('fs');const vm=require('vm');const ts=(()=>{try{return require('typescript')}catch{return require('/opt/nvm/versions/node/v22.16.0/lib/node_modules/typescript')}})();const assert=require('assert');
const source=fs.readFileSync('data/curriculum.ts','utf8');
const res=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020},reportDiagnostics:true});
assert.equal((res.diagnostics||[]).filter(x=>x.category===ts.DiagnosticCategory.Error).length,0,'Curriculum should parse');
const box={exports:{}};vm.runInNewContext(res.outputText,box);const data=box.exports;
assert.equal(data.phases.length,12,'12 phases');assert.equal(data.phases.reduce((a,p)=>a+p.topics.length,0),72,'72 topics');assert.equal(data.projects.length,12,'12 projects');assert.ok(data.lessons.length>=4,'starter lessons');assert.equal(data.quiz.length,4,'knowledge check');
assert.ok(data.lessons.every(l=>l.sections.length>=3),'lesson depth');assert.ok(data.phases.every(p=>p.topics.length===6),'each phase covers six topics');
for(const file of ['components/LearningPlatform.tsx','app/page.tsx','app/layout.tsx']){
 const text=fs.readFileSync(file,'utf8');const parsed=ts.transpileModule(text,{fileName:file,compilerOptions:{jsx:ts.JsxEmit.Preserve,module:ts.ModuleKind.ESNext},reportDiagnostics:true});const problems=(parsed.diagnostics||[]).filter(d=>d.category===ts.DiagnosticCategory.Error);assert.equal(problems.length,0,`${file}: ${problems.map(x=>x.messageText)}`);
}
for(const path of ['public/brand/saire-pcb.png','public/brand/saire-symbol.png','public/brand/saire-horizontal.png','public/preview/index.html','public/preview/preview.css','public/preview/preview.js'])assert.ok(fs.existsSync(path),`${path} exists`);
const page=fs.readFileSync('public/preview/index.html','utf8');assert.ok(page.includes('data.js')&&page.includes('preview.js'));
console.log('PASS: 12 phases, 72 topics, 12 milestones, four starter lessons, quiz, image assets, TSX syntax, offline preview assets.');
// Simulate an offline browser DOM enough to smoke-test initial navigation output.
const root={innerHTML:'',addEventListener(event,fn){this['on'+event]=fn}};
const document={querySelector(q){if(q==='#app')return root;return null},getElementById(){return null},createElement(){return {click(){}}}};
const store={};const localStorage={getItem:k=>store[k]||null,setItem:(k,v)=>store[k]=v};
const window={SAIRE_DATA:data,scrollTo(){},addEventListener(){}};
const script=fs.readFileSync('public/preview/preview.js','utf8');
vm.runInNewContext(script,{window,document,localStorage,setTimeout(){},console,Blob:class{},URL:{createObjectURL(){return''},revokeObjectURL(){}},navigator:{},}, {timeout:5000});
assert.ok(root.innerHTML.includes('Engineer the future.'));
const makeClick=(action,more={})=>({target:{closest(){return {dataset:{action,...more}}}}});
root.onclick(makeClick('roadmap'));assert.ok(root.innerHTML.includes('Programming Fundamentals'));
root.onclick(makeClick('go',{to:'classroom'}));assert.ok(root.innerHTML.includes('What is programming, really?'));
root.onclick(makeClick('projects'));assert.ok(root.innerHTML.includes('Business Expense Manager'));
root.onclick(makeClick('planner'));assert.ok(root.innerHTML.includes('Weekly study planner'));
root.onclick(makeClick('resources'));assert.ok(root.innerHTML.includes('Official Python Tutorial'));
root.onclick(makeClick('go',{to:'classroom'}));
for(const [i,a] of [1,0,2,2].entries())root.onclick(makeClick('answer',{q:String(i),a:String(a)}));
root.onclick(makeClick('submit'));
assert.ok(root.innerHTML.includes('Score:')&&root.innerHTML.includes('4/4'));
root.onclick(makeClick('finish'));
assert.ok(JSON.parse(store['saire-linked-lms-v1']).completed.includes('p1-l1'),'completed lesson is persisted');
console.log('PASS: standalone preview renders six sections, scores a 4/4 quiz and saves lesson completion.');
