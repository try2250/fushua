Page({
  data: {
    correctRate: 0,
    correctCount: 0,
    wrongCount: 0,
    totalQuestions: 0,
    streak: 0
  },

  onLoad(options) {
    this.setData({
      correctCount: parseInt(options.correct) || 0,
      wrongCount: parseInt(options.wrong) || 0,
      totalQuestions: parseInt(options.total) || 0,
    });
    const total = this.data.totalQuestions;
    this.setData({
      correctRate: total > 0 ? Math.round((this.data.correctCount / total) * 100) : 0
    });
    this.loadStreak();
  },

  loadStreak() {
    try {
      const app = getApp();
      if (app.getUserInfo && app.getUserInfo().streak) {
        this.setData({ streak: app.getUserInfo().streak });
      }
    } catch (e) {}
  },

  handleRestart() {
    wx.navigateBack();
  },

  handleBack() {
    wx.switchTab({ url: '/pages/tabbar/practice/practice' });
  }
});
