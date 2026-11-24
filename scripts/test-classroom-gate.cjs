/* Regression coverage for the learner-facing locked/empty distinction. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const ts = require('typescript');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');

const filename = path.resolve(__dirname, '../components/ClassroomGate.tsx');
const compiled = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
  compilerOptions: {module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX},
}).outputText;
const loaded = new Module(filename, module);
loaded.filename = filename;
loaded.paths = Module._nodeModulePaths(path.dirname(filename));
loaded._compile(compiled, filename);
const Gate = loaded.exports.default;
const render = props => renderToStaticMarkup(React.createElement(Gate, {onRoadmap() {}, ...props}));

const locked = render({lessonCount: 4, entry: {
  kind: 'prerequisite', title: 'Start with the required foundation', message: 'Complete the shared Python module.',
  requirements: [{module_id: 1, title: 'Python foundation', course_slug: 'python', status: 'lessons'}],
  action: {label: 'Open Python foundation classroom', href: '/dashboard/?course=python&view=classroom&lesson=one'},
}});
assert.match(locked, /4 published lessons/);
assert.match(locked, /Required modules, in order/);
assert.match(locked, /Open Python foundation classroom/);
assert.match(locked, /view=classroom/);
assert.doesNotMatch(locked, /No lesson is available/);
assert.match(locked, /does not start a timer/);
const empty = render({lessonCount: 0, entry: {kind: 'empty', requirements: [], action: null}});
assert.match(empty, /no published lessons yet/);
assert.doesNotMatch(empty, /published lessons in this course/);
const fallback = render({lessonCount: 4});
assert.match(fallback, /locked by module requirements/);
assert.doesNotMatch(fallback, /no published lessons yet/);
const review = render({lessonCount: 2, entry: {kind: 'review', title: 'Awaiting review', message: 'Your project is awaiting review.',
  requirements: [], action: {label: 'View submitted project', href: '/assignments/?assignment=foundation-final'}}});
assert.match(review, /View submitted project/);
assert.doesNotMatch(review, /Start 14-day lesson/);
console.log('PASS: locked foundation link, true empty course, older-API fallback and pending-review classroom states.');
