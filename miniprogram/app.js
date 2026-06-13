// app.js
App({
  onLaunch() {
    // 小程序启动时执行
    console.log('付刷小程序启动');

    // 检查登录状态
    this.checkLoginStatus();
  },

  checkLoginStatus() {
    const token = wx.getStorageSync('token');
    if (token) {
      // 验证 token 是否有效
      this.globalData.isLoggedIn = true;
    } else {
      this.globalData.isLoggedIn = false;
    }
  },

  globalData: {
    isLoggedIn: false,
    userInfo: null,
    apiBaseUrl: 'https://www.fushua.asia/api/v1'
  }
});
