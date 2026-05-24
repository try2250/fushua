// pages/teacher/create-assignment/create-assignment.js
const request = require('../../../utils/request');

Page({
  data: {
    classes: [],
    questions: [],
    selectedQuestions: [],
    formData: {
      title: '',
      class_id: null,
      deadline: ''
    },
    classIndex: 0,
    selectedClassName: '请选择班级',
    dateValue: '',
    timeValue: ''
  },

  onLoad() {
    this.loadClasses();
    this.loadQuestions();
    this.initDateTime();
  },

  initDateTime() {
    const now = new Date();
    const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000);

    const year = tomorrow.getFullYear();
    const month = (tomorrow.getMonth() + 1).toString().padStart(2, '0');
    const day = tomorrow.getDate().toString().padStart(2, '0');
    const dateValue = `${year}-${month}-${day}`;

    const timeValue = '23:59';

    this.setData({
      dateValue,
      timeValue
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
    } catch (error) {
      console.error('加载班级列表失败:', error);
    }
  },

  async loadQuestions() {
    try {
      const res = await request.get('/api/v1/questions');
      this.setData({
        questions: (res || []).map(item => this.decorateQuestion(item))
      });
    } catch (error) {
      console.error('加载题目列表失败:', error);
    }
  },

  handleTitleInput(e) {
    this.setData({
      'formData.title': e.detail.value
    });
  },

  handleClassChange(e) {
    const index = parseInt(e.detail.value, 10) || 0;
    const selectedClass = this.data.classes[index] || null;
    const classId = selectedClass ? selectedClass.id : null;
    this.setData({
      classIndex: index,
      'formData.class_id': classId,
      selectedClassName: selectedClass ? selectedClass.name : '请选择班级'
    });
  },

  handleDateChange(e) {
    this.setData({
      dateValue: e.detail.value
    });
  },

  handleTimeChange(e) {
    this.setData({
      timeValue: e.detail.value
    });
  },

  handleQuestionToggle(e) {
    const { id } = e.currentTarget.dataset;
    const selectedQuestions = [...this.data.selectedQuestions];
    const index = selectedQuestions.indexOf(id);

    if (index > -1) {
      selectedQuestions.splice(index, 1);
    } else {
      selectedQuestions.push(id);
    }

    this.setData({
      selectedQuestions,
      questions: this.data.questions.map(item => ({
        ...item,
        selected: selectedQuestions.includes(item.id)
      }))
    });
  },

  isQuestionSelected(questionId) {
    return this.data.selectedQuestions.includes(questionId);
  },

  getClassName(classes, index) {
    const selectedClass = classes[index];
    return selectedClass ? selectedClass.name : '请选择班级';
  },

  decorateQuestion(question) {
    const qType = question.type || question.q_type;
    const difficulty = question.difficulty;
    let difficultyText = '困难';

    if (difficulty === 'easy' || difficulty === 1) {
      difficultyText = '简单';
    } else if (difficulty === 'medium' || difficulty === 2) {
      difficultyText = '中等';
    }

    return {
      ...question,
      selected: this.data.selectedQuestions.includes(question.id),
      typeText: qType === 'single' || qType === 'choice' ? '单选题' : '多选题',
      difficultyText
    };
  },

  async handleSubmit() {
    const { title, class_id } = this.data.formData;
    const { dateValue, timeValue, selectedQuestions } = this.data;

    // 验证表单
    if (!title.trim()) {
      wx.showToast({
        title: '请输入作业标题',
        icon: 'none'
      });
      return;
    }

    if (!class_id) {
      wx.showToast({
        title: '请选择班级',
        icon: 'none'
      });
      return;
    }

    if (selectedQuestions.length === 0) {
      wx.showToast({
        title: '请至少选择一道题目',
        icon: 'none'
      });
      return;
    }

    if (!dateValue || !timeValue) {
      wx.showToast({
        title: '请设置截止时间',
        icon: 'none'
      });
      return;
    }

    // 组合日期和时间
    const deadline = `${dateValue} ${timeValue}:00`;

    try {
      wx.showLoading({ title: '创建中...' });

      await request.post('/api/v1/assignments', {
        title: title.trim(),
        class_id,
        question_ids: selectedQuestions,
        deadline
      });

      wx.hideLoading();
      wx.showToast({
        title: '创建成功',
        icon: 'success'
      });

      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
    } catch (error) {
      wx.hideLoading();
      console.error('创建作业失败:', error);
      wx.showToast({
        title: error.message || '创建失败',
        icon: 'none'
      });
    }
  }
});
