// pages/teacher/students/students.js
const request = require('../../../utils/request');

Page({
  data: {
    students: [],
    classes: [],
    selectedClassId: null,
    classIndex: 0,
    selectedClassName: '请选择班级',
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
      const classes = res || [];

      this.setData({
        classes,
        selectedClassName: this.getClassName(classes, this.data.classIndex)
      });

      if (classes.length > 0) {
        this.setData({
          selectedClassId: classes[0].id,
          selectedClassName: classes[0].name || '请选择班级'
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
      const classInfo = res || {};

      // 获取每个学生的统计数据
      const students = classInfo.students || classInfo.members || [];
      const studentsWithStats = await Promise.all(
        students.map(async (student) => {
          try {
            const statsRes = await request.get(`/api/v1/users/${student.id}/stats`);
            return {
              ...student,
              avatarText: this.getAvatarText(student),
              stats: statsRes || {}
            };
          } catch (error) {
            console.error(`加载学生 ${student.id} 统计失败:`, error);
            return {
              ...student,
              avatarText: this.getAvatarText(student),
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
    const index = parseInt(e.detail.value, 10) || 0;
    const selectedClass = this.data.classes[index] || null;
    const classId = selectedClass ? selectedClass.id : null;

    this.setData({
      classIndex: index,
      selectedClassId: classId,
      selectedClassName: selectedClass ? selectedClass.name : '请选择班级'
    });

    this.loadStudents();
  },

  goToStudentDetail(e) {
    const { id } = e.currentTarget.dataset;
    wx.navigateTo({
      url: `/pages/teacher/student-detail/student-detail?id=${id}`
    });
  },

  getClassName(classes, index) {
    const selectedClass = classes[index];
    return selectedClass ? selectedClass.name : '请选择班级';
  },

  getAvatarText(student) {
    const username = student && student.username ? student.username : '';
    return username ? username.slice(0, 1) : '学';
  }
});
