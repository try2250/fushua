const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');

function read(relativePath) {
  return fs.readFileSync(path.join(root, relativePath), 'utf8');
}

const appWxss = read('miniprogram/app.wxss');
const appJson = JSON.parse(read('miniprogram/app.json'));

assert.match(appWxss, /--academy-green:\s*#176B57/i);
assert.match(appWxss, /--ink-title:\s*#2A2118/i);
assert.match(appWxss, /--paper-bg:\s*#F7EEDC/i);
assert.match(appWxss, /--seal-red:\s*#B8322A/i);
assert.match(appWxss, /--gild:\s*#B9853D/i);
assert.match(appWxss, /ledger-card/);
assert.match(appWxss, /seal-badge/);
assert.match(appWxss, /ink-note/);
assert.match(appWxss, /paper-texture/);
assert.match(appWxss, /landscape-wash/);

assert.equal(appJson.window.navigationBarBackgroundColor.toLowerCase(), '#176b57');
assert.equal(appJson.tabBar.selectedColor.toLowerCase(), '#176b57');
assert.equal(appJson.tabBar.backgroundColor.toLowerCase(), '#fbf5e8');

const themedPages = [
  'miniprogram/pages/tabbar/practice/practice.wxss',
  'miniprogram/pages/tabbar/assignments/assignments.wxss',
  'miniprogram/pages/tabbar/mistakes/mistakes.wxss',
  'miniprogram/pages/tabbar/profile/profile.wxss',
  'miniprogram/pages/assignment-detail/assignment-detail.wxss',
  'miniprogram/pages/teacher/classes/classes.wxss',
  'miniprogram/pages/teacher/class-detail/class-detail.wxss',
  'miniprogram/pages/teacher/assignments/assignments.wxss',
  'miniprogram/pages/teacher/create-assignment/create-assignment.wxss',
  'miniprogram/pages/teacher/students/students.wxss',
  'miniprogram/pages/teacher/student-detail/student-detail.wxss',
];

for (const page of themedPages) {
  const css = read(page);
  assert.match(css, /var\(--academy-green\)|#176B57/i, `${page} should use academy green theme`);
  assert.match(css, /var\(--paper-card\)|ledger-card|paper|文墨学苑/i, `${page} should use paper academy language`);
}

console.log('miniprogram UI theme tests passed');
