// pages/index/index.js
const auth = require('../../utils/auth');

Page({
  data: {
    isLoggedIn: false,
    userInfo: null
  },

  onLoad() {
    // 检查登录状态
    this.checkLoginStatus();
  },

  onShow() {
    // 每次显示页面时检查登录状态
    this.checkLoginStatus();
  },

  checkLoginStatus() {
    const isLoggedIn = auth.isLoggedIn();
    const userInfo = auth.getUserInfo();

    this.setData({
      isLoggedIn,
      userInfo
    });

    // 如果已登录，根据角色跳转到对应页面
    if (isLoggedIn && userInfo) {
      if (userInfo.role === 'student') {
        wx.switchTab({
          url: '/pages/tabbar/practice/practice'
        });
      } else if (userInfo.role === 'teacher') {
        wx.switchTab({
          url: '/pages/tabbar/assignments/assignments'
        });
      }
    }
  },

  goToLogin() {
    wx.navigateTo({
      url: '/pages/login/login'
    });
  }
});
