// pages/tabbar/assignments/assignments.js
const { request } = require('../../../utils/request');
const auth = require('../../../utils/auth');

Page({
  data: {
    assignments: [],
    loading: false,
    currentTab: 'pending', // pending, completed, all
    tabs: [
      { key: 'pending', label: '待完成' },
      { key: 'completed', label: '已完成' },
      { key: 'all', label: '全部' }
    ]
  },

  onLoad() {
    this.loadAssignments();
  },

  onShow() {
    // 每次显示时刷新列表
    this.loadAssignments();
  },

  /**
   * 切换标签
   */
  handleTabChange(e) {
    const { tab } = e.currentTarget.dataset;
    this.setData({ currentTab: tab });
    this.loadAssignments();
  },

  /**
   * 加载作业列表
   */
  async loadAssignments() {
    if (this.data.loading) return;

    this.setData({ loading: true });

    try {
      const { currentTab } = this.data;
      const params = {};

      if (currentTab === 'pending') {
        params.status = 'pending';
      } else if (currentTab === 'completed') {
        params.status = 'completed';
      }

      const res = await request('/api/v1/assignments', {
        method: 'GET',
        data: params
      });

      if (res) {
        this.setData({
          assignments: res.map(item => ({
            ...item,
            // 格式化日期
            deadline_formatted: this.formatDate(item.deadline),
            // 计算进度
            progress: item.total_questions > 0
              ? Math.round((item.completed_questions / item.total_questions) * 100)
              : 0
          }))
        });
      }
    } catch (error) {
      console.error('加载作业列表失败:', error);
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 格式化日期
   */
  formatDate(dateString) {
    if (!dateString) return '';

    const date = new Date(dateString);
    const now = new Date();
    const diff = date.getTime() - now.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days < 0) {
      return '已截止';
    } else if (days === 0) {
      return '今天截止';
    } else if (days === 1) {
      return '明天截止';
    } else if (days <= 7) {
      return `${days}天后截止`;
    } else {
      const month = date.getMonth() + 1;
      const day = date.getDate();
      return `${month}月${day}日截止`;
    }
  },

  /**
   * 跳转到作业详情
   */
  handleViewAssignment(e) {
    const { id } = e.currentTarget.dataset;
    wx.navigateTo({
      url: `/pages/assignment-detail/assignment-detail?id=${id}`
    });
  },

  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    this.loadAssignments().then(() => {
      wx.stopPullDownRefresh();
    });
  }
});
