// utils/storage.js

/**
 * 设置本地存储
 * @param {string} key - 键名
 * @param {any} value - 值
 * @returns {boolean}
 */
function setStorage(key, value) {
  try {
    wx.setStorageSync(key, value);
    return true;
  } catch (e) {
    console.error(`设置存储失败 [${key}]:`, e);
    return false;
  }
}

/**
 * 获取本地存储
 * @param {string} key - 键名
 * @param {any} defaultValue - 默认值
 * @returns {any}
 */
function getStorage(key, defaultValue = null) {
  try {
    const value = wx.getStorageSync(key);
    return value !== '' ? value : defaultValue;
  } catch (e) {
    console.error(`获取存储失败 [${key}]:`, e);
    return defaultValue;
  }
}

/**
 * 移除本地存储
 * @param {string} key - 键名
 * @returns {boolean}
 */
function removeStorage(key) {
  try {
    wx.removeStorageSync(key);
    return true;
  } catch (e) {
    console.error(`移除存储失败 [${key}]:`, e);
    return false;
  }
}

/**
 * 清空本地存储
 * @returns {boolean}
 */
function clearStorage() {
  try {
    wx.clearStorageSync();
    return true;
  } catch (e) {
    console.error('清空存储失败:', e);
    return false;
  }
}

/**
 * 获取存储信息
 * @returns {object|null}
 */
function getStorageInfo() {
  try {
    return wx.getStorageInfoSync();
  } catch (e) {
    console.error('获取存储信息失败:', e);
    return null;
  }
}

module.exports = {
  setStorage,
  getStorage,
  removeStorage,
  clearStorage,
  getStorageInfo
};
