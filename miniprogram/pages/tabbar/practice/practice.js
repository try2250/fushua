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
    }
  },

  onLoad() {
    this.loadTodayStats();
    this.loadQuestions();
  },

  /**
   * 加载今日统计数据
   */
  async loadTodayStats() {
    try {
      const res = await request({
        url: '/api/v1/practice-records/today-stats',
        method: 'GET'
      });

      if (res.success && res.data) {
        this.setData({
          todayStats: {
            completed: res.data.completed || 0,
            correct: res.data.correct || 0,
            total: res.data.total || 0
          }
        });
      }
    } catch (error) {
      console.error('加载今日统计失败:', error);
    }
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

      const res = await request({
        url: '/api/v1/questions/random',
        method: 'GET',
        data: params
      });

      if (res.success && res.data && res.data.length > 0) {
        this.setData({
          questions: res.data,
          totalQuestions: res.data.length,
          currentIndex: 0,
          currentQuestion: res.data[0],
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
      await request({
        url: '/api/v1/practice-records',
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
      this.setData({
        todayStats: {
          completed: todayStats.completed + 1,
          correct: isCorrect ? todayStats.correct + 1 : todayStats.correct,
          total: todayStats.total + 1
        }
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
      // 已完成所有题目
      wx.showModal({
        title: '完成',
        content: '已完成本轮刷题，是否继续？',
        success: (res) => {
          if (res.confirm) {
            this.loadQuestions();
          }
        }
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
