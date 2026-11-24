// Run in a separate Node process so the TypeScript loader is scoped to this test.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const React = require('react');
const {renderToStaticMarkup} = require('react-dom/server');
const ts = require('typescript');
const root = path.resolve(__dirname, '..');
const resolve = Module._resolveFilename;
Module._resolveFilename = function(name, ...args) {
  return resolve.call(this, name.startsWith('@/') ? path.join(root, name.slice(2)) : name, ...args);
};
for (const extension of ['.ts', '.tsx']) {
  require.extensions[extension] = (module, filename) => {
    const source = fs.readFileSync(filename, 'utf8');
    const compiled = ts.transpileModule(source, {compilerOptions: {
      target: ts.ScriptTarget.ES2020, module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX,
    }});
    module._compile(compiled.outputText, filename);
  };
}
const {count, timeframe, dashboardDestination} = require('../lib/academy-display');
const Nav = require('../components/AcademyNavigation').default;
const Workspace = require('../components/DashboardWorkspace').default;
const render = (component, props) => renderToStaticMarkup(React.createElement(component, props));
assert.equal(count(0, 'question'), '0 questions');
assert.equal(count(1, 'lesson'), '1 lesson');
assert.equal(count(2, 'project'), '2 projects');
for (const [input, result] of [['12–18', '12–18 months'], ['12-18', '12-18 months'], ['1', '1 month'], ['2 months', '2 months'], ['', 'To be confirmed']]) {
  assert.equal(timeframe(input), result);
}
const requested = '/dashboard/?course=python&view=roadmap#module-2';
assert.equal(dashboardDestination(requested), requested);
for (const value of [null, 'https://outside.invalid/dashboard/', '//outside.invalid/dashboard/', '/accounts/login/']) {
  assert.equal(dashboardDestination(value), '/dashboard/');
}
const navigation = render(Nav, {course: 'python', active: 'roadmap'});
for (const title of ['Workspace', 'Smart Classroom', 'Engineering Lab', 'ProofLoop Centre', 'Learning Twin', 'Support']) assert.ok(navigation.includes(title));
assert.match(navigation, /view=roadmap&amp;course=python" aria-current="page"/);
assert.match(render(Nav, {compact:true}), /<summary>Academy menu/);
assert.match(render(Nav, {demo:true}), /\/demo\/\?view=roadmap/);
const live = {
  username: 'Demo learner', orientation: {acknowledged:true}, projects: [],
  iterations: {second: {status:'supplementary', due_at:'2026-11-08T12:00:00Z', supplementary_due_at:'2026-11-15T12:00:00Z'}},
  course: {slug:'python', title:'Programming foundations', estimated_months:'1', phases:[{id:1},{id:2}],
    lessons:[{id:'first', title:'First lesson', phaseId:1}, {id:'second', title:'Working with files', phaseId:1}]}
};
const workspace = () => render(Workspace, {live, openLesson() {}, roadmap() {}});
assert.match(workspace(), /<h2>Working with files<\/h2>/);
assert.match(workspace(), /Resume lesson/);
assert.match(workspace(), /dateTime="2026-11-15T12:00:00Z"/i);
assert.match(workspace(), /1 module with lessons · 1 outline · 1 month/);
live.course.phases[0].progress = {project_unlocked:true, final_project:{slug:'files',title:'File index',status:'ready'}};
live.projects = [{assignment:'files',due_at:'2026-11-23T12:00:00Z',submissions:[]}];
assert.match(workspace(), /assignment=files#project-mentor/);
live.course.phases[0].progress.project_unlocked = false;
assert.doesNotMatch(workspace(), /assignment=files#project-mentor/);
live.orientation.acknowledged = false;
assert.match(workspace(), /Open the handbook/);
live.orientation.acknowledged = true;
live.course.lessons = [];
assert.match(workspace(), /Explore your course roadmap/);
assert.doesNotMatch(workspace(), /Resume lesson/);
console.log('PASS: count and duration copy, return destinations, grouped navigation, and dashboard learner states.');
