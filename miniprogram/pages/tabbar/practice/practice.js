// pages/tabbar/practice/practice.js
const { request } = require('../../../utils/request');
const auth = require('../../../utils/auth');

Page({
  data: {
    currentQuestion: null,
    currentIndex: 0,
    totalQuestions: 0,
    questions: [],
    userAnswer: null,
    showResult: false,
    isCorrect: false,
    loading: false,

    // 筛选条件
    filters: {
      subject: '',
      semester: '',
      chapter: ''
    },

    // 统计数据
    todayStats: {
      completed: 0,
      correct: 0,
      total: 0
    },
    todayCorrectRate: 0,
    streak: 0
  },

  onLoad() {
    this.loadTodayStats();
    this.loadStreak();
    this.loadQuestions();
  },

  async loadStreak() {
    try {
      const res = await request('/api/v1/practice-records/today-stats', { method: 'GET' });
      if (res && res.streak !== undefined) {
        this.setData({ streak: res.streak });
      }
    } catch (error) {
      console.error('加载 streak 失败:', error);
    }
  },

  /**
   * 加载今日统计数据
   */
  async loadTodayStats() {
    try {
      const res = await request('/api/v1/practice-records/today-stats', {
        method: 'GET'
      });

      if (res) {
        this.setTodayStats(res);
      }
    } catch (error) {
      console.error('加载今日统计失败:', error);
    }
  },

  setTodayStats(stats) {
    const completed = stats.completed || 0;
    const correct = stats.correct || 0;
    const total = stats.total || 0;
    const todayCorrectRate = total > 0 ? Math.round((correct / total) * 100) : 0;

    this.setData({
      todayStats: {
        completed,
        correct,
        total
      },
      todayCorrectRate
    });
  },

  /**
   * 加载题目列表
   */
  async loadQuestions() {
    if (this.data.loading) return;

    this.setData({ loading: true });

    try {
      const { subject, semester, chapter } = this.data.filters;
      const params = {
        count: 10
      };

      if (subject) params.subject = subject;
      if (semester) params.semester = semester;
      if (chapter) params.chapter = chapter;

      const res = await request('/api/v1/questions/random', {
        method: 'GET',
        data: params
      });

      if (res && res.length > 0) {
        this.setData({
          questions: res,
          totalQuestions: res.length,
          currentIndex: 0,
          currentQuestion: res[0],
          userAnswer: null,
          showResult: false
        });
      } else {
        wx.showToast({
          title: '暂无题目',
          icon: 'none'
        });
      }
    } catch (error) {
      console.error('加载题目失败:', error);
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 选择答案
   */
  handleSelectAnswer(e) {
    if (this.data.showResult) return;

    const { answer } = e.currentTarget.dataset;
    this.setData({ userAnswer: answer });
  },

  /**
   * 提交答案
   */
  async handleSubmitAnswer() {
    if (!this.data.userAnswer) {
      wx.showToast({
        title: '请选择答案',
        icon: 'none'
      });
      return;
    }

    const { currentQuestion, userAnswer } = this.data;
    const isCorrect = userAnswer === currentQuestion.correct_answer;

    this.setData({
      showResult: true,
      isCorrect
    });

    // 提交答题记录
    try {
      await request('/api/v1/practice-records', {
        method: 'POST',
        data: {
          question_id: currentQuestion.id,
          user_answer: userAnswer,
          is_correct: isCorrect,
          time_spent: 0 // 可以添加计时功能
        }
      });

      // 更新今日统计
      const { todayStats } = this.data;
      this.setTodayStats({
        completed: todayStats.completed + 1,
        correct: isCorrect ? todayStats.correct + 1 : todayStats.correct,
        total: todayStats.total + 1
      });
    } catch (error) {
      console.error('提交答题记录失败:', error);
    }
  },

  /**
   * 下一题
   */
  handleNextQuestion() {
    const { currentIndex, questions } = this.data;

    if (currentIndex < questions.length - 1) {
      // 还有题目
      this.setData({
        currentIndex: currentIndex + 1,
        currentQuestion: questions[currentIndex + 1],
        userAnswer: null,
        showResult: false,
        isCorrect: false
      });
    } else {
      // 已完成所有题目 → 跳转总结页
      const correct = this.data.questions.filter(q => q.userAnswer === q.correct_answer).length;
      const wrong = this.data.totalQuestions - correct;
      wx.redirectTo({
        url: `/pages/tabbar/practice/summary?correct=${correct}&wrong=${wrong}&total=${this.data.totalQuestions}`
      });
    }
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
   * 查看解析
   */
  handleViewExplanation() {
    const { currentQuestion } = this.data;

    wx.showModal({
      title: '题目解析',
      content: currentQuestion.explanation || '暂无解析',
      showCancel: false
    });
  },

  /**
   * 收藏题目
   */
  async handleCollectQuestion() {
    wx.showToast({
      title: '收藏功能开发中',
      icon: 'none'
    });
  }
});
