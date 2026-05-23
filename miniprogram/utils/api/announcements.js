// api/announcements.js - 公告相关API

const { baseUrl, timeout } = require('../config');
const app = getApp();

/**
 * 获取当前用户的公告列表
 */
function getAnnouncements() {
  return new Promise((resolve, reject) => {
    const token = wx.getStorageSync('token');
    const userInfo = wx.getStorageSync('userInfo');

    if (!token || !userInfo) {
      reject(new Error('未登录'));
      return;
    }

    wx.request({
      url: `${baseUrl}/announcements`,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      timeout,
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(res.data);
        } else {
          reject(new Error(res.data.detail || '获取公告失败'));
        }
      },
      fail: (err) => {
        reject(err);
      }
    });
  });
}

module.exports = {
  getAnnouncements
};
