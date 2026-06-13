const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');

function read(relativePath) {
  return fs.readFileSync(path.join(root, relativePath), 'utf8');
}

const benchmarkFiles = [
  'miniprogram/pages/login/login',
  'miniprogram/pages/tabbar/practice/practice',
  'miniprogram/pages/teacher/classes/classes',
];

for (const file of benchmarkFiles) {
  const wxml = read(`${file}.wxml`);
  const wxss = read(`${file}.wxss`);

  assert.doesNotMatch(wxss, /#667eea|#764ba2|#1890ff/i, `${file}.wxss should not use old blue/purple theme colors`);
  assert.match(wxss, /academy-green|landscape-wash|academy/i, `${file}.wxss should use the Product Design academy visual language`);
  assert.match(wxml, /academy|landscape|seal|ledger|brush/i, `${file}.wxml should expose academy-specific structure`);
}

assert.match(read('miniprogram/pages/login/login.wxml'), /文墨学苑|中学题库/);
assert.match(read('miniprogram/pages/tabbar/practice/practice.wxml'), /学生学习旅程|自主学习/);
assert.match(read('miniprogram/pages/teacher/classes/classes.wxml'), /教师管理旅程|班级台账/);

console.log('miniprogram product design benchmark page tests passed');
