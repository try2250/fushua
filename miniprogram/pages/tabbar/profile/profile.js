// pages/tabbar/profile/profile.js
const auth = require('../../../utils/auth');
const { request } = require('../../../utils/request');

Page({
  data: {
    userInfo: null,
    avatarText: '用',
    isStudent: false,
    isTeacher: false,
    stats: {
      totalQuestions: 0,
      correctRate: 0,
      totalAssignments: 0,
      completedAssignments: 0
    }
  },

  onLoad() {
    this.loadUserInfo();
  },

  onShow() {
    // 每次显示页面时刷新用户信息
    this.loadUserInfo();
  },

  /**
   * 加载用户信息
   */
  async loadUserInfo() {
    try {
      const userInfo = auth.getUserInfo();

      if (!userInfo) {
        wx.showToast({
          title: '请先登录',
          icon: 'none'
        });
        setTimeout(() => {
          wx.reLaunch({
            url: '/pages/login/login'
          });
        }, 1500);
        return;
      }

      this.setData({
        userInfo,
        avatarText: this.getAvatarText(userInfo),
        isStudent: auth.isStudent(),
        isTeacher: auth.isTeacher()
      });

      // 加载统计数据
      if (auth.isStudent()) {
        await this.loadStudentStats();
      }
    } catch (error) {
      console.error('加载用户信息失败:', error);
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
    }
  },

  getAvatarText(userInfo) {
    const username = userInfo && userInfo.username ? userInfo.username : '';
    return username ? username.slice(0, 1) : '用';
  },

  /**
   * 加载学生统计数据
   */
  async loadStudentStats() {
    try {
      const res = await request('/api/v1/users/me/stats', {
        method: 'GET'
      });

      if (res) {
        this.setData({
          stats: {
            totalQuestions: res.total_questions || 0,
            correctRate: res.correct_rate || 0,
            totalAssignments: res.total_assignments || 0,
            completedAssignments: res.completed_assignments || 0
          }
        });
      }
    } catch (error) {
      console.error('加载统计数据失败:', error);
      // 统计数据加载失败不影响页面显示
    }
  },

  /**
   * 退出登录
   */
  handleLogout() {
    wx.showModal({
      title: '提示',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          auth.logout();
          wx.reLaunch({
            url: '/pages/login/login'
          });
        }
      }
    });
  },

  /**
   * 跳转到个人信息编辑页
   */
  handleEditProfile() {
    wx.showToast({
      title: '功能开发中',
      icon: 'none'
    });
  },

  /**
   * 跳转到设置页
   */
  handleSettings() {
    wx.showToast({
      title: '功能开发中',
      icon: 'none'
    });
  },

  /**
   * 跳转到关于页面
   */
  handleAbout() {
    wx.showToast({
      title: '功能开发中',
      icon: 'none'
    });
  }
});
