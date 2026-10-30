// Generate a browser-readable copy of the shared course data for the dependency-free demo.
const fs = require('fs');
const ts = (()=>{try{return require('typescript')}catch{return require('/opt/nvm/versions/node/v22.16.0/lib/node_modules/typescript')}})();
const vm = require('vm');
const source = fs.readFileSync('data/curriculum.ts','utf8');
const js = ts.transpileModule(source, { compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020} }).outputText;
const ctx={exports:{}};
vm.runInNewContext(js,ctx);
fs.writeFileSync('public/preview/data.js', 'window.SAIRE_DATA = '+JSON.stringify(ctx.exports)+';\n');
console.log('Wrote public/preview/data.js');
