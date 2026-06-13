// pages/bind/bind.js
const { post, get } = require('../../utils/request');
const auth = require('../../utils/auth');
const { validatePhone, validateCode } = require('../../utils/util');
const config = require('../../config');

Page({
  data: {
    openid_token: '',
    phone: '',
    code: '',
    role: 'student',
    class_id: '',
    invite_code: '',
    classes: [],
    countdown: 0,
    loading: false,
    step: 1,  // 1: 输入手机号和验证码, 2: 选择角色和班级
    phoneBindingRequireSms: config.APP_CONFIG.phoneBindingRequireSms  // 是否需要短信验证
  },

  onLoad(options) {
    if (options.openid_token) {
      this.setData({
        openid_token: options.openid_token
      });
    } else {
      wx.showToast({
        title: '参数错误',
        icon: 'none'
      });
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
    }
  },

  /**
   * 输入手机号
   */
  onPhoneInput(e) {
    this.setData({
      phone: e.detail.value
    });
  },

  /**
   * 输入验证码
   */
  onCodeInput(e) {
    this.setData({
      code: e.detail.value
    });
  },

  /**
   * 发送验证码
   */
  sendCode() {
    const { phone, countdown } = this.data;

    if (countdown > 0) return;

    if (!validatePhone(phone)) {
      wx.showToast({
        title: '请输入正确的手机号',
        icon: 'none'
      });
      return;
    }

    post('/auth/sms/send', {
      phone,
      purpose: 'bind'
    })
      .then(() => {
        wx.showToast({
          title: '验证码已发送',
          icon: 'success'
        });

        // 开始倒计时
        this.startCountdown();
      })
      .catch((err) => {
        console.error('发送验证码失败:', err);
      });
  },

  /**
   * 开始倒计时
   */
  startCountdown() {
    this.setData({
      countdown: config.APP_CONFIG.smsCountdown
    });

    const timer = setInterval(() => {
      const countdown = this.data.countdown - 1;
      if (countdown <= 0) {
        clearInterval(timer);
        this.setData({ countdown: 0 });
      } else {
        this.setData({ countdown });
      }
    }, 1000);
  },

  /**
   * 下一步：验证手机号和验证码
   */
  nextStep() {
    const { phone, code } = this.data;

    if (!validatePhone(phone)) {
      wx.showToast({
        title: '请输入正确的手机号',
        icon: 'none'
      });
      return;
    }

    // 如果开发期不需要验证码，跳过验证码校验
    if (!config.APP_CONFIG.phoneBindingRequireSms) {
      this.setData({ step: 2 });
      if (this.data.role === 'student') {
        this.loadClasses();
      }
      return;
    }

    if (!validateCode(code)) {
      wx.showToast({
        title: '请输入6位验证码',
        icon: 'none'
      });
      return;
    }

    // 进入第二步：选择角色
    this.setData({ step: 2 });

    // 如果是学生，加载班级列表
    if (this.data.role === 'student') {
      this.loadClasses();
    }
  },

  /**
   * 选择角色
   */
  onRoleChange(e) {
    const role = e.detail.value;
    this.setData({ role });

    // 如果切换到学生，加载班级列表
    if (role === 'student') {
      this.loadClasses();
    }
  },

  /**
   * 选择班级
   */
  onClassChange(e) {
    this.setData({
      class_id: parseInt(e.detail.value)
    });
  },

  /**
   * 输入邀请码
   */
  onInviteCodeInput(e) {
    this.setData({
      invite_code: e.detail.value
    });
  },

  /**
   * 加载班级列表
   */
  loadClasses() {
    get('/classes', {}, { showError: false })
      .then((data) => {
        this.setData({
          classes: data || []
        });
      })
      .catch((err) => {
        console.error('加载班级列表失败:', err);
      });
  },

  /**
   * 提交绑定
   */
  handleBind() {
    const { openid_token, phone, code, role, class_id, invite_code, loading } = this.data;

    if (loading) return;

    // 验证
    if (role === 'student' && !class_id) {
      wx.showToast({
        title: '请选择班级',
        icon: 'none'
      });
      return;
    }

    if (role === 'teacher' && !invite_code) {
      wx.showToast({
        title: '请输入邀请码',
        icon: 'none'
      });
      return;
    }

    this.setData({ loading: true });

    post('/auth/wechat/bind', {
      openid_token,
      phone,
      code,
      role,
      class_id: role === 'student' ? class_id : null,
      invite_code: role === 'teacher' ? invite_code : null
    })
      .then((data) => {
        this.setData({ loading: false });

        // 保存 token 和用户信息
        auth.saveToken(data.token);
        auth.saveUserInfo(data.user);

        wx.showToast({
          title: '绑定成功',
          icon: 'success',
          duration: 1500
        });

        setTimeout(() => {
          this.redirectToHome();
        }, 1500);
      })
      .catch((err) => {
        console.error('绑定失败:', err);
        this.setData({ loading: false });
      });
  },

  /**
   * 跳转到首页
   */
  redirectToHome() {
    const role = this.data.role;
    if (role === 'student') {
      wx.switchTab({
        url: '/pages/tabbar/practice/practice'
      });
    } else if (role === 'teacher') {
      wx.switchTab({
        url: '/pages/tabbar/assignments/assignments'
      });
    } else {
      wx.switchTab({
        url: '/pages/tabbar/profile/profile'
      });
    }
  }
});
