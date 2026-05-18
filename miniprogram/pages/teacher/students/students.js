// pages/teacher/students/students.js
const request = require('../../../utils/request');

Page({
  data: {
    students: [],
    classes: [],
    selectedClassId: null,
    classIndex: 0,
    loading: false
  },

  onLoad() {
    this.loadClasses();
  },

  onPullDownRefresh() {
    this.loadStudents().then(() => {
      wx.stopPullDownRefresh();
    });
  },

  async loadClasses() {
    try {
      const res = await request.get('/api/v1/classes');
      const classes = res.data || [];

      this.setData({
        classes
      });

      if (classes.length > 0) {
        this.setData({
          selectedClassId: classes[0].id
        });
        this.loadStudents();
      }
    } catch (error) {
      console.error('加载班级列表失败:', error);
    }
  },

  async loadStudents() {
    if (!this.data.selectedClassId) return;

    this.setData({ loading: true });
    try {
      const res = await request.get(`/api/v1/classes/${this.data.selectedClassId}`);
      const classInfo = res.data;

      // 获取每个学生的统计数据
      const students = classInfo.students || [];
      const studentsWithStats = await Promise.all(
        students.map(async (student) => {
          try {
            const statsRes = await request.get(`/api/v1/users/${student.id}/stats`);
            return {
              ...student,
              stats: statsRes.data || {}
            };
          } catch (error) {
            console.error(`加载学生 ${student.id} 统计失败:`, error);
            return {
              ...student,
              stats: {}
            };
          }
        })
      );

      this.setData({
        students: studentsWithStats,
        loading: false
      });
    } catch (error) {
      console.error('加载学生列表失败:', error);
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
      this.setData({ loading: false });
    }
  },

  handleClassChange(e) {
    const index = parseInt(e.detail.value);
    const classId = this.data.classes[index]?.id || null;

    this.setData({
      classIndex: index,
      selectedClassId: classId
    });

    this.loadStudents();
  },

  goToStudentDetail(e) {
    const { id } = e.currentTarget.dataset;
    wx.navigateTo({
      url: `/pages/teacher/student-detail/student-detail?id=${id}`
    });
  }
});
