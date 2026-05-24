// pages/teacher/classes/classes.js
const { request } = require('../../../utils/request');
const auth = require('../../../utils/auth');

Page({
  data: {
    classes: [],
    loading: false
  },

  onLoad() {
    // 检查是否为教师
    if (!auth.isTeacher()) {
      wx.showToast({
        title: '仅教师可访问',
        icon: 'none'
      });
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
      return;
    }

    this.loadClasses();
  },

  onShow() {
    this.loadClasses();
  },

  /**
   * 加载班级列表
   */
  async loadClasses() {
    if (this.data.loading) return;

    this.setData({ loading: true });

    try {
      const res = await request('/api/v1/classes', {
        method: 'GET'
      });

      if (res) {
        this.setData({
          classes: res.map(this.decorateClass)
        });
      }
    } catch (error) {
      console.error('加载班级列表失败:', error);
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
    } finally {
      this.setData({ loading: false });
    }
  },

  decorateClass(item) {
    const name = item && item.name ? item.name : '';
    return {
      ...item,
      iconText: name ? name.slice(0, 2) : '班级'
    };
  },

  /**
   * 跳转到创建班级页面
   */
  handleCreateClass() {
    wx.navigateTo({
      url: '/pages/teacher/create-class/create-class'
    });
  },

  /**
   * 跳转到班级详情
   */
  handleViewClass(e) {
    const { id } = e.currentTarget.dataset;
    wx.navigateTo({
      url: `/pages/teacher/class-detail/class-detail?id=${id}`
    });
  },

  /**
   * 编辑班级
   */
  handleEditClass(e) {
    const { id, name } = e.currentTarget.dataset;

    wx.navigateTo({
      url: `/pages/teacher/create-class/create-class?id=${id}&name=${encodeURIComponent(name)}`
    });
  },

  /**
   * 删除班级
   */
  handleDeleteClass(e) {
    const { id, name } = e.currentTarget.dataset;

    wx.showModal({
      title: '确认删除',
      content: `确定要删除班级"${name}"吗？删除后无法恢复。`,
      confirmColor: '#ff4d4f',
      success: async (res) => {
        if (res.confirm) {
          try {
            await request(`/api/v1/classes/${id}`, {
              method: 'DELETE'
            });

            wx.showToast({
              title: '删除成功',
              icon: 'success'
            });

            this.loadClasses();
          } catch (error) {
            console.error('删除班级失败:', error);
            wx.showToast({
              title: '删除失败',
              icon: 'none'
            });
          }
        }
      }
    });
  },

  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    this.loadClasses().then(() => {
      wx.stopPullDownRefresh();
    });
  }
});
