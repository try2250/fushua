const assert = require('node:assert/strict');
const { buildUrl, BASE_URL } = require('../miniprogram/utils/request');

assert.equal(BASE_URL, 'https://www.fushua.asia');
assert.equal(buildUrl('/api/v1/classes'), 'https://www.fushua.asia/api/v1/classes');
assert.equal(buildUrl('/auth/login'), 'https://www.fushua.asia/api/v1/auth/login');
assert.equal(buildUrl('questions/random'), 'https://www.fushua.asia/api/v1/questions/random');

console.log('miniprogram request url tests passed');
