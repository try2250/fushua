// pages/teacher/assignment-detail/assignment-detail.js
const request = require('../../../utils/request');

Page({
  data: {
    assignmentId: null,
    assignment: null,
    records: [],
    submittedCount: 0,
    totalStudents: 0,
    completionRate: 0,
    averageScore: 0,
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
        assignment: this.decorateAssignment(res)
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
      const records = (res || []).map(item => this.decorateRecord(item));
      const stats = this.calculateStats(records);

      this.setData({
        records,
        ...stats,
        loading: false
      });
    } catch (error) {
      console.error('加载提交记录失败:', error);
      this.setData({ loading: false });
    }
  },

  decorateAssignment(assignment) {
    if (!assignment) return null;
    return {
      ...assignment,
      deadlineFormatted: this.formatDate(assignment.deadline)
    };
  },

  decorateRecord(record) {
    const studentName = record.student_name || '';
    return {
      ...record,
      avatarText: studentName ? studentName.slice(0, 1) : '学',
      submittedAtFormatted: this.formatDate(record.submitted_at)
    };
  },

  calculateStats(records) {
    const totalStudents = records.length;
    const submittedCount = records.filter(r => r.submitted_at).length;
    const completionRate = totalStudents === 0 ? 0 : Math.round((submittedCount / totalStudents) * 100);
    const submittedRecords = records.filter(r => r.submitted_at && r.score !== null);
    const scoreTotal = submittedRecords.reduce((sum, r) => sum + r.score, 0);
    const averageScore = submittedRecords.length === 0 ? 0 : Math.round(scoreTotal / submittedRecords.length);

    return {
      submittedCount,
      totalStudents,
      completionRate,
      averageScore
    };
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
