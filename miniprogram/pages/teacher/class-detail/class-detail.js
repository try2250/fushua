// pages/teacher/class-detail/class-detail.js
const { request } = require('../../../utils/request');

Page({
  data: {
    classId: null,
    classInfo: null,
    members: [],
    loading: false,
    currentTab: 'members' // members, stats
  },

  onLoad(options) {
    const { id } = options;
    if (id) {
      this.setData({ classId: parseInt(id) });
      this.loadClassDetail();
    }
  },

  /**
   * 加载班级详情
   */
  async loadClassDetail() {
    if (this.data.loading) return;

    this.setData({ loading: true });

    try {
      const res = await request(`/api/v1/classes/${this.data.classId}`, {
        method: 'GET'
      });

      if (res) {
        const members = res.members || res.students || [];
        this.setData({
          classInfo: res,
          members: members.map(this.decorateMember)
        });
      }
    } catch (error) {
      console.error('加载班级详情失败:', error);
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
    } finally {
      this.setData({ loading: false });
    }
  },

  decorateMember(member) {
    const username = member && member.username ? member.username : '';
    return {
      ...member,
      avatarText: username ? username.slice(0, 1) : '学'
    };
  },

  /**
   * 切换标签
   */
  handleTabChange(e) {
    const { tab } = e.currentTarget.dataset;
    this.setData({ currentTab: tab });
  },

  /**
   * 查看学生详情
   */
  handleViewStudent(e) {
    const { id } = e.currentTarget.dataset;
    wx.showToast({
      title: '学生详情功能开发中',
      icon: 'none'
    });
  },

  /**
   * 移除学生
   */
  handleRemoveStudent(e) {
    const { id, name } = e.currentTarget.dataset;

    wx.showModal({
      title: '确认移除',
      content: `确定要将"${name}"移出班级吗？`,
      confirmColor: '#ff4d4f',
      success: async (res) => {
        if (res.confirm) {
          try {
            await request(`/api/v1/classes/${this.data.classId}/members/${id}`, {
              method: 'DELETE'
            });

            wx.showToast({
              title: '移除成功',
              icon: 'success'
            });

            this.loadClassDetail();
          } catch (error) {
            console.error('移除学生失败:', error);
            wx.showToast({
              title: '移除失败',
              icon: 'none'
            });
          }
        }
      }
    });
  },

  /**
   * 分享班级邀请码
   */
  handleShareInvite() {
    const { classInfo } = this.data;

    wx.showModal({
      title: '班级邀请码',
      content: `邀请码：${classInfo.invite_code || '暂无'}\n\n学生可在绑定页面输入此邀请码加入班级`,
      showCancel: false
    });
  },

  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    this.loadClassDetail().then(() => {
      wx.stopPullDownRefresh();
    });
  }
});
