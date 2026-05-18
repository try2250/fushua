// pages/tabbar/mistakes/mistakes.js
const { request } = require('../../../utils/request');

Page({
  data: {
    mistakes: [],
    loading: false,
    filters: {
      subject: '',
      chapter: ''
    }
  },

  onLoad() {
    this.loadMistakes();
  },

  onShow() {
    this.loadMistakes();
  },

  /**
   * 加载错题列表
   */
  async loadMistakes() {
    if (this.data.loading) return;

    this.setData({ loading: true });

    try {
      const { subject, chapter } = this.data.filters;
      const params = {};

      if (subject) params.subject = subject;
      if (chapter) params.chapter = chapter;

      const res = await request({
        url: '/api/v1/practice-records/mistakes',
        method: 'GET',
        data: params
      });

      if (res.success && res.data) {
        this.setData({
          mistakes: res.data.map(item => ({
            ...item,
            // 计算错误次数
            mistake_count: item.mistake_count || 1,
            // 最后练习时间
            last_practice: this.formatDate(item.updated_at)
          }))
        });
      }
    } catch (error) {
      console.error('加载错题失败:', error);
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
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) {
      return '今天';
    } else if (days === 1) {
      return '昨天';
    } else if (days < 7) {
      return `${days}天前`;
    } else {
      const month = date.getMonth() + 1;
      const day = date.getDate();
      return `${month}月${day}日`;
    }
  },

  /**
   * 查看题目详情
   */
  handleViewQuestion(e) {
    const { question } = e.currentTarget.dataset;

    wx.showModal({
      title: '题目详情',
      content: question.content,
      showCancel: false
    });
  },

  /**
   * 重新练习
   */
  handlePracticeAgain(e) {
    const { id } = e.currentTarget.dataset;

    wx.showToast({
      title: '功能开发中',
      icon: 'none'
    });
  },

  /**
   * 移出错题本
   */
  handleRemoveMistake(e) {
    const { id } = e.currentTarget.dataset;

    wx.showModal({
      title: '确认',
      content: '确定要将此题移出错题本吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await request({
              url: `/api/v1/practice-records/${id}/remove-mistake`,
              method: 'POST'
            });

            wx.showToast({
              title: '已移出',
              icon: 'success'
            });

            this.loadMistakes();
          } catch (error) {
            console.error('移出失败:', error);
            wx.showToast({
              title: '操作失败',
              icon: 'none'
            });
          }
        }
      }
    });
  },

  /**
   * 打开筛选器
   */
  handleOpenFilter() {
    wx.showToast({
      title: '筛选功能开发中',
      icon: 'none'
    });
  },

  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    this.loadMistakes().then(() => {
      wx.stopPullDownRefresh();
    });
  }
});
