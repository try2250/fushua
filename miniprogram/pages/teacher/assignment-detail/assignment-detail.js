// pages/teacher/assignment-detail/assignment-detail.js
const request = require('../../../utils/request');

Page({
  data: {
    assignmentId: null,
    assignment: null,
    records: [],
    loading: false
  },

  onLoad(options) {
    if (options.id) {
      this.setData({
        assignmentId: parseInt(options.id)
      });
      this.loadAssignmentDetail();
      this.loadRecords();
    }
  },

  onPullDownRefresh() {
    Promise.all([
      this.loadAssignmentDetail(),
      this.loadRecords()
    ]).then(() => {
      wx.stopPullDownRefresh();
    });
  },

  async loadAssignmentDetail() {
    try {
      const res = await request.get(`/api/v1/assignments/${this.data.assignmentId}`);
      this.setData({
        assignment: res.data
      });
    } catch (error) {
      console.error('加载作业详情失败:', error);
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
    }
  },

  async loadRecords() {
    this.setData({ loading: true });
    try {
      const res = await request.get(`/api/v1/assignments/${this.data.assignmentId}/records`);
      this.setData({
        records: res.data || [],
        loading: false
      });
    } catch (error) {
      console.error('加载提交记录失败:', error);
      this.setData({ loading: false });
    }
  },

  formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const hour = date.getHours();
    const minute = date.getMinutes();
    return `${month}月${day}日 ${hour}:${minute.toString().padStart(2, '0')}`;
  },

  getSubmittedCount() {
    return this.data.records.filter(r => r.submitted_at).length;
  },

  getTotalStudents() {
    return this.data.records.length;
  },

  getCompletionRate() {
    const total = this.getTotalStudents();
    if (total === 0) return 0;
    const submitted = this.getSubmittedCount();
    return Math.round((submitted / total) * 100);
  },

  getAverageScore() {
    const submittedRecords = this.data.records.filter(r => r.submitted_at && r.score !== null);
    if (submittedRecords.length === 0) return 0;
    const totalScore = submittedRecords.reduce((sum, r) => sum + r.score, 0);
    return Math.round(totalScore / submittedRecords.length);
  },

  handleViewRecord(e) {
    const { id } = e.currentTarget.dataset;
    wx.showToast({
      title: '查看详情功能开发中',
      icon: 'none'
    });
  }
});
