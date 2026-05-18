// utils/auth.js

/**
 * 保存 token
 * @param {string} token - JWT token
 */
function saveToken(token) {
  try {
    wx.setStorageSync('token', token);
    return true;
  } catch (e) {
    console.error('保存 token 失败:', e);
    return false;
  }
}

/**
 * 获取 token
 * @returns {string|null}
 */
function getToken() {
  try {
    return wx.getStorageSync('token') || null;
  } catch (e) {
    console.error('获取 token 失败:', e);
    return null;
  }
}

/**
 * 清除 token
 */
function clearToken() {
  try {
    wx.removeStorageSync('token');
    return true;
  } catch (e) {
    console.error('清除 token 失败:', e);
    return false;
  }
}

/**
 * 保存用户信息
 * @param {object} userInfo - 用户信息
 */
function saveUserInfo(userInfo) {
  try {
    wx.setStorageSync('userInfo', userInfo);
    return true;
  } catch (e) {
    console.error('保存用户信息失败:', e);
    return false;
  }
}

/**
 * 获取用户信息
 * @returns {object|null}
 */
function getUserInfo() {
  try {
    return wx.getStorageSync('userInfo') || null;
  } catch (e) {
    console.error('获取用户信息失败:', e);
    return null;
  }
}

/**
 * 清除用户信息
 */
function clearUserInfo() {
  try {
    wx.removeStorageSync('userInfo');
    return true;
  } catch (e) {
    console.error('清除用户信息失败:', e);
    return false;
  }
}

/**
 * 检查是否已登录
 * @returns {boolean}
 */
function isLoggedIn() {
  const token = getToken();
  return !!token;
}

/**
 * 登出
 */
function logout() {
  clearToken();
  clearUserInfo();

  wx.showToast({
    title: '已退出登录',
    icon: 'success',
    duration: 1500
  });

  setTimeout(() => {
    wx.redirectTo({
      url: '/pages/login/login'
    });
  }, 1500);
}

/**
 * 检查登录状态，未登录则跳转登录页
 * @returns {boolean}
 */
function checkLogin() {
  if (!isLoggedIn()) {
    wx.showToast({
      title: '请先登录',
      icon: 'none',
      duration: 1500
    });

    setTimeout(() => {
      wx.redirectTo({
        url: '/pages/login/login'
      });
    }, 1500);

    return false;
  }
  return true;
}

/**
 * 获取用户角色
 * @returns {string|null} - 'student' | 'teacher' | 'admin' | null
 */
function getUserRole() {
  const userInfo = getUserInfo();
  return userInfo ? userInfo.role : null;
}

/**
 * 检查是否是学生
 * @returns {boolean}
 */
function isStudent() {
  return getUserRole() === 'student';
}

/**
 * 检查是否是教师
 * @returns {boolean}
 */
function isTeacher() {
  return getUserRole() === 'teacher';
}

/**
 * 检查是否是管理员
 * @returns {boolean}
 */
function isAdmin() {
  return getUserRole() === 'admin';
}

module.exports = {
  saveToken,
  getToken,
  clearToken,
  saveUserInfo,
  getUserInfo,
  clearUserInfo,
  isLoggedIn,
  logout,
  checkLogin,
  getUserRole,
  isStudent,
  isTeacher,
  isAdmin
};
