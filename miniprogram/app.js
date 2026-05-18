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
    apiBaseUrl: 'https://your-api-domain.com/api/v1'  // 需要替换为实际的 API 地址
  }
});
