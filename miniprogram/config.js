// config.js - 小程序配置文件

// API 配置
const API_CONFIG = {
  // 开发环境 API 地址
  development: {
    baseUrl: 'http://localhost:8000',
    timeout: 10000
  },

  // 生产环境 API 地址
  production: {
    baseUrl: 'https://www.fushua.asia',
    timeout: 10000
  }
};

// 当前环境（development | production）
const ENV = 'production';

// 导出当前环境配置
const config = API_CONFIG[ENV];

// 微信小程序配置
const WECHAT_CONFIG = {
  appId: 'wx86db4c7584917750'
};

// 其他配置
const APP_CONFIG = {
  // 验证码倒计时（秒）
  smsCountdown: 60,

  // 开发期是否需要短信验证码（与后端配置保持一致）
  phoneBindingRequireSms: false,

  // 每页显示数量
  pageSize: 20,

  // 图片上传大小限制（MB）
  maxImageSize: 5,

  // 主题色
  primaryColor: '#176B57',

  // 成功色
  successColor: '#52c41a',

  // 错误色
  errorColor: '#ff4d4f',

  // 警告色
  warningColor: '#faad14'
};

module.exports = {
  ...config,
  ENV,
  WECHAT_CONFIG,
  APP_CONFIG
};
