// pages/teacher/create-class/create-class.js
const { request } = require('../../../utils/request');

Page({
  data: {
    classId: null,
    className: '',
    isEdit: false
  },

  onLoad(options) {
    const { id, name } = options;

    if (id) {
      // 编辑模式
      this.setData({
        classId: parseInt(id),
        className: decodeURIComponent(name || ''),
        isEdit: true
      });
    }
  },

  /**
   * 输入班级名称
   */
  handleInputName(e) {
    this.setData({
      className: e.detail.value
    });
  },

  /**
   * 提交表单
   */
  async handleSubmit() {
    const { classId, className, isEdit } = this.data;

    // 验证
    if (!className.trim()) {
      wx.showToast({
        title: '请输入班级名称',
        icon: 'none'
      });
      return;
    }

    wx.showLoading({ title: isEdit ? '保存中...' : '创建中...' });

    try {
      if (isEdit) {
        // 更新班级
        await request({
          url: `/api/v1/classes/${classId}`,
          method: 'PUT',
          data: {
            name: className.trim()
          }
        });

        wx.showToast({
          title: '保存成功',
          icon: 'success'
        });
      } else {
        // 创建班级
        await request({
          url: '/api/v1/classes',
          method: 'POST',
          data: {
            name: className.trim()
          }
        });

        wx.showToast({
          title: '创建成功',
          icon: 'success'
        });
      }

      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
    } catch (error) {
      wx.hideLoading();
      console.error('操作失败:', error);
      wx.showToast({
        title: isEdit ? '保存失败' : '创建失败',
        icon: 'none'
      });
    }
  }
});
