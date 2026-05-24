// pages/assignment-detail/assignment-detail.js
const { request } = require('../../utils/request');

Page({
  data: {
    assignmentId: null,
    assignment: null,
    questions: [],
    currentIndex: 0,
    currentQuestion: null,
    userAnswer: null,
    showResult: false,
    isCorrect: false,
    loading: false,
    answers: {} // 存储所有答案 {questionId: answer}
  },

  onLoad(options) {
    const { id } = options;
    if (id) {
      this.setData({ assignmentId: id });
      this.loadAssignmentDetail();
    }
  },

  /**
   * 加载作业详情
   */
  async loadAssignmentDetail() {
    this.setData({ loading: true });

    try {
      const res = await request(`/api/v1/assignments/${this.data.assignmentId}`, {
        method: 'GET'
      });

      if (res) {
        const assignment = res;
        const questions = assignment.questions || [];

        this.setData({
          assignment,
          questions,
          currentQuestion: questions[0] || null,
          currentIndex: 0
        });

        // 如果已完成，加载已提交的答案
        if (assignment.status === 'completed') {
          await this.loadSubmittedAnswers();
        }
      }
    } catch (error) {
      console.error('加载作业详情失败:', error);
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 加载已提交的答案
   */
  async loadSubmittedAnswers() {
    try {
      const res = await request(`/api/v1/assignments/${this.data.assignmentId}/submission`, {
        method: 'GET'
      });

      if (res) {
        const answers = {};
        const submittedAnswers = res.answers || [];
        submittedAnswers.forEach(item => {
          answers[item.question_id] = item.user_answer;
        });
        this.setData({ answers });
      }
    } catch (error) {
      console.error('加载答案失败:', error);
    }
  },

  /**
   * 选择答案
   */
  handleSelectAnswer(e) {
    if (this.data.assignment.status === 'completed') return;

    const { answer } = e.currentTarget.dataset;
    const { currentQuestion, answers } = this.data;

    answers[currentQuestion.id] = answer;

    this.setData({
      userAnswer: answer,
      answers
    });
  },

  /**
   * 上一题
   */
  handlePrevQuestion() {
    const { currentIndex, questions, answers } = this.data;

    if (currentIndex > 0) {
      const newIndex = currentIndex - 1;
      const newQuestion = questions[newIndex];

      this.setData({
        currentIndex: newIndex,
        currentQuestion: newQuestion,
        userAnswer: answers[newQuestion.id] || null,
        showResult: false
      });
    }
  },

  /**
   * 下一题
   */
  handleNextQuestion() {
    const { currentIndex, questions, answers } = this.data;

    if (currentIndex < questions.length - 1) {
      const newIndex = currentIndex + 1;
      const newQuestion = questions[newIndex];

      this.setData({
        currentIndex: newIndex,
        currentQuestion: newQuestion,
        userAnswer: answers[newQuestion.id] || null,
        showResult: false
      });
    }
  },

  /**
   * 提交作业
   */
  handleSubmitAssignment() {
    const { questions, answers } = this.data;

    // 检查是否所有题目都已作答
    const unansweredCount = questions.filter(q => !answers[q.id]).length;

    if (unansweredCount > 0) {
      wx.showModal({
        title: '提示',
        content: `还有${unansweredCount}道题未作答，确定要提交吗？`,
        success: (res) => {
          if (res.confirm) {
            this.submitAnswers();
          }
        }
      });
    } else {
      wx.showModal({
        title: '确认提交',
        content: '提交后将无法修改答案，确定要提交吗？',
        success: (res) => {
          if (res.confirm) {
            this.submitAnswers();
          }
        }
      });
    }
  },

  /**
   * 提交答案
   */
  async submitAnswers() {
    wx.showLoading({ title: '提交中...' });

    try {
      const { assignmentId, answers } = this.data;

      // 转换答案格式
      const answersList = Object.keys(answers).map(questionId => ({
        question_id: parseInt(questionId),
        user_answer: answers[questionId]
      }));

      const res = await request(`/api/v1/assignments/${assignmentId}/submit`, {
        method: 'POST',
        data: {
          answers: answersList
        }
      });

      wx.hideLoading();

      if (res) {
        wx.showModal({
          title: '提交成功',
          content: `得分：${res.score || 0}分`,
          showCancel: false,
          success: () => {
            // 重新加载作业详情
            this.loadAssignmentDetail();
          }
        });
      }
    } catch (error) {
      wx.hideLoading();
      console.error('提交作业失败:', error);
      wx.showToast({
        title: '提交失败',
        icon: 'none'
      });
    }
  },

  /**
   * 查看解析
   */
  handleViewExplanation() {
    const { currentQuestion } = this.data;

    if (this.data.assignment.status !== 'completed') {
      wx.showToast({
        title: '提交后可查看解析',
        icon: 'none'
      });
      return;
    }

    wx.showModal({
      title: '题目解析',
      content: currentQuestion.explanation || '暂无解析',
      showCancel: false
    });
  }
});
