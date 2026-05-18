// pages/login/login.js
const { post } = require('../../utils/request');
const auth = require('../../utils/auth');

Page({
  data: {
    loading: false
  },

  onLoad() {
    // 检查是否已登录
    if (auth.isLoggedIn()) {
      this.redirectToHome();
    }
  },

  /**
   * 微信登录
   */
  handleWechatLogin() {
    if (this.data.loading) return;

    this.setData({ loading: true });

    // 调用微信登录
    wx.login({
      success: (res) => {
        if (res.code) {
          this.loginWithCode(res.code);
        } else {
          wx.showToast({
            title: '获取登录凭证失败',
            icon: 'none'
          });
          this.setData({ loading: false });
        }
      },
      fail: (err) => {
        console.error('wx.login 失败:', err);
        wx.showToast({
          title: '微信登录失败',
          icon: 'none'
        });
        this.setData({ loading: false });
      }
    });
  },

  /**
   * 使用 code 登录
   */
  loginWithCode(code) {
    post('/auth/wechat/login', { code }, { showLoading: false })
      .then((data) => {
        this.setData({ loading: false });

        if (data.need_bind) {
          // 需要绑定手机号，跳转到绑定页面
          wx.navigateTo({
            url: `/pages/bind/bind?openid_token=${data.openid_token}`
          });
        } else {
          // 已注册，保存 token 和用户信息
          auth.saveToken(data.token);
          auth.saveUserInfo(data.user);

          wx.showToast({
            title: '登录成功',
            icon: 'success',
            duration: 1500
          });

          setTimeout(() => {
            this.redirectToHome();
          }, 1500);
        }
      })
      .catch((err) => {
        console.error('登录失败:', err);
        this.setData({ loading: false });
      });
  },

  /**
   * 跳转到首页
   */
  redirectToHome() {
    const userInfo = auth.getUserInfo();
    if (userInfo) {
      if (userInfo.role === 'student') {
        wx.switchTab({
          url: '/pages/tabbar/practice/practice'
        });
      } else if (userInfo.role === 'teacher') {
        wx.switchTab({
          url: '/pages/tabbar/assignments/assignments'
        });
      } else {
        wx.switchTab({
          url: '/pages/tabbar/profile/profile'
        });
      }
    } else {
      wx.switchTab({
        url: '/pages/tabbar/practice/practice'
      });
    }
  }
});
