// utils/request.js
const config = require('../config');

// API 基础 URL
const BASE_URL = config.baseUrl;

/**
 * 封装的请求方法
 * @param {string} url - 请求路径（不包含 base url）
 * @param {object} options - 请求配置
 * @returns {Promise}
 */
function request(url, options = {}) {
  return new Promise((resolve, reject) => {
    // 获取 token
    const token = wx.getStorageSync('token');

    // 显示加载提示
    if (options.showLoading !== false) {
      wx.showLoading({
        title: '加载中...',
        mask: true
      });
    }

    wx.request({
      url: BASE_URL + url,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
        ...options.header
      },
      success: (res) => {
        wx.hideLoading();

        // 统一响应格式处理
        if (res.statusCode === 200) {
          if (res.data.code === 0) {
            // 请求成功
            resolve(res.data.data);
          } else if (res.data.code === 20001 || res.data.code === 20002 || res.data.code === 20003) {
            // Token 无效或过期，跳转登录
            wx.showToast({
              title: '登录已过期，请重新登录',
              icon: 'none',
              duration: 2000
            });

            // 清除 token
            wx.removeStorageSync('token');
            wx.removeStorageSync('userInfo');

            // 跳转到登录页
            setTimeout(() => {
              wx.redirectTo({
                url: '/pages/login/login'
              });
            }, 2000);

            reject(res.data);
          } else {
            // 业务错误
            if (options.showError !== false) {
              wx.showToast({
                title: res.data.message || '请求失败',
                icon: 'none',
                duration: 2000
              });
            }
            reject(res.data);
          }
        } else {
          // HTTP 错误
          wx.showToast({
            title: `请求失败 (${res.statusCode})`,
            icon: 'none',
            duration: 2000
          });
          reject(res);
        }
      },
      fail: (err) => {
        wx.hideLoading();

        if (options.showError !== false) {
          wx.showToast({
            title: '网络请求失败',
            icon: 'none',
            duration: 2000
          });
        }

        reject(err);
      }
    });
  });
}

/**
 * GET 请求
 */
function get(url, data = {}, options = {}) {
  return request(url, {
    method: 'GET',
    data,
    ...options
  });
}

/**
 * POST 请求
 */
function post(url, data = {}, options = {}) {
  return request(url, {
    method: 'POST',
    data,
    ...options
  });
}

/**
 * PUT 请求
 */
function put(url, data = {}, options = {}) {
  return request(url, {
    method: 'PUT',
    data,
    ...options
  });
}

/**
 * DELETE 请求
 */
function del(url, data = {}, options = {}) {
  return request(url, {
    method: 'DELETE',
    data,
    ...options
  });
}

module.exports = {
  request,
  get,
  post,
  put,
  del,
  BASE_URL
};
