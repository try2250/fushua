// pages/teacher/student-detail/student-detail.js
const request = require('../../../utils/request');

Page({
  data: {
    studentId: null,
    student: null,
    avatarText: '学',
    stats: null,
    accuracyRate: 0,
    mistakes: [],
    loading: false
  },

  onLoad(options) {
    if (options.id) {
      this.setData({
        studentId: parseInt(options.id)
      });
      this.loadStudentDetail();
      this.loadStudentStats();
      this.loadStudentMistakes();
    }
  },

  onPullDownRefresh() {
    Promise.all([
      this.loadStudentDetail(),
      this.loadStudentStats(),
      this.loadStudentMistakes()
    ]).then(() => {
      wx.stopPullDownRefresh();
    });
  },

  async loadStudentDetail() {
    try {
      const res = await request.get(`/api/v1/users/${this.data.studentId}`);
      this.setData({
        student: res,
        avatarText: this.getAvatarText(res)
      });
    } catch (error) {
      console.error('加载学生信息失败:', error);
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
    }
  },

  async loadStudentStats() {
    try {
      const res = await request.get(`/api/v1/users/${this.data.studentId}/stats`);
      this.setData({
        stats: res,
        accuracyRate: this.calculateAccuracyRate(res)
      });
    } catch (error) {
      console.error('加载学生统计失败:', error);
    }
  },

  async loadStudentMistakes() {
    this.setData({ loading: true });
    try {
      const res = await request.get(`/api/v1/users/${this.data.studentId}/mistakes`);
      this.setData({
        mistakes: res || [],
        loading: false
      });
    } catch (error) {
      console.error('加载错题列表失败:', error);
      this.setData({ loading: false });
    }
  },

  getAccuracyRate() {
    if (!this.data.stats) return 0;
    const { total_practice, correct_count } = this.data.stats;
    if (total_practice === 0) return 0;
    return Math.round((correct_count / total_practice) * 100);
  },

  getAvatarText(student) {
    const username = student && student.username ? student.username : '';
    return username ? username.slice(0, 1) : '学';
  },

  calculateAccuracyRate(stats) {
    if (!stats) return 0;
    const totalPractice = stats.total_practice || 0;
    const correctCount = stats.correct_count || 0;
    if (totalPractice === 0) return 0;
    return Math.round((correctCount / totalPractice) * 100);
  }
});
