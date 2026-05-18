// pages/teacher/assignments/assignments.js
const request = require('../../../utils/request');

Page({
  data: {
    assignments: [],
    classes: [],
    selectedClassId: null,
    loading: false
  },

  onLoad() {
    this.loadClasses();
    this.loadAssignments();
  },

  onPullDownRefresh() {
    this.loadAssignments().then(() => {
      wx.stopPullDownRefresh();
    });
  },

  async loadClasses() {
    try {
      const res = await request.get('/api/v1/classes');
      this.setData({
        classes: res.data || []
      });
    } catch (error) {
      console.error('加载班级列表失败:', error);
    }
  },

  async loadAssignments() {
    this.setData({ loading: true });
    try {
      const params = {};
      if (this.data.selectedClassId) {
        params.class_id = this.data.selectedClassId;
      }

      const res = await request.get('/api/v1/assignments', { params });
      this.setData({
        assignments: res.data || [],
        loading: false
      });
    } catch (error) {
      console.error('加载作业列表失败:', error);
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
      this.setData({ loading: false });
    }
  },

  handleClassChange(e) {
    const classId = e.detail.value === 'all' ? null : parseInt(e.detail.value);
    this.setData({
      selectedClassId: classId
    });
    this.loadAssignments();
  },

  goToCreateAssignment() {
    wx.navigateTo({
      url: '/pages/teacher/create-assignment/create-assignment'
    });
  },

  goToAssignmentDetail(e) {
    const { id } = e.currentTarget.dataset;
    wx.navigateTo({
      url: `/pages/teacher/assignment-detail/assignment-detail?id=${id}`
    });
  },

  async handleDeleteAssignment(e) {
    const { id, title } = e.currentTarget.dataset;

    const res = await wx.showModal({
      title: '确认删除',
      content: `确定要删除作业"${title}"吗？此操作不可恢复。`
    });

    if (!res.confirm) return;

    try {
      await request.delete(`/api/v1/assignments/${id}`);
      wx.showToast({
        title: '删除成功',
        icon: 'success'
      });
      this.loadAssignments();
    } catch (error) {
      console.error('删除作业失败:', error);
      wx.showToast({
        title: '删除失败',
        icon: 'none'
      });
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

  getStatusText(assignment) {
    const now = new Date();
    const deadline = new Date(assignment.deadline);

    if (now > deadline) {
      return '已截止';
    }
    return '进行中';
  },

  getStatusClass(assignment) {
    const now = new Date();
    const deadline = new Date(assignment.deadline);

    if (now > deadline) {
      return 'status-ended';
    }
    return 'status-active';
  }
});
