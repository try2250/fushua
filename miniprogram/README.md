# 付刷微信小程序

## 项目简介

付刷微信小程序是基于 FastAPI 后端的刷题学习平台，支持学生端和教师端功能。

## 技术栈

- 微信小程序原生开发
- FastAPI RESTful API
- JWT 认证

## 项目结构

```
miniprogram/
├── pages/                    # 页面
│   ├── index/                # 首页
│   ├── login/                # 登录页
│   ├── bind/                 # 绑定页
│   ├── tabbar/               # 底部导航页面
│   │   ├── practice/         # 刷题（学生）
│   │   ├── assignments/      # 作业
│   │   ├── mistakes/         # 错题本
│   │   └── profile/          # 个人中心
│   └── assignment-detail/    # 作业详情
├── components/               # 组件
│   ├── question-card/        # 题目卡片
│   └── loading/              # 加载组件
├── utils/                    # 工具函数
│   ├── request.js            # API 请求封装
│   ├── auth.js               # 认证管理
│   ├── storage.js            # 本地存储
│   └── util.js               # 通用工具
├── images/                   # 图片资源
├── app.js                    # 小程序入口
├── app.json                  # 小程序配置
├── app.wxss                  # 全局样式
├── project.config.json       # 项目配置
└── sitemap.json              # 站点地图
```

## 开发指南

### 1. 环境准备

1. 下载并安装[微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)
2. 注册微信小程序账号，获取 AppID
3. 配置后端 API 地址

### 2. 配置说明

#### 2.1 修改 AppID

编辑 `project.config.json`，将 `appid` 字段修改为你的小程序 AppID：

```json
{
  "appid": "your-appid-here"
}
```

#### 2.2 配置 API 地址

编辑 `utils/request.js`，修改 `BASE_URL` 为你的后端 API 地址：

```javascript
const BASE_URL = 'https://your-api-domain.com/api/v1';
```

或者编辑 `app.js`，修改 `globalData.apiBaseUrl`：

```javascript
globalData: {
  apiBaseUrl: 'https://your-api-domain.com/api/v1'
}
```

### 3. 开发流程

1. 使用微信开发者工具打开 `miniprogram` 目录
2. 在工具中预览和调试
3. 真机调试前需要配置服务器域名白名单

### 4. 服务器域名配置

在微信公众平台 - 开发 - 开发管理 - 开发设置 - 服务器域名中配置：

- **request 合法域名**：你的后端 API 域名（必须是 HTTPS）
- **uploadFile 合法域名**：如果有文件上传功能
- **downloadFile 合法域名**：如果有文件下载功能

### 5. 图标资源

需要准备以下图标（放在 `images/` 目录）：

- `logo.png` - 应用 Logo
- `practice.png` / `practice-active.png` - 刷题图标
- `assignment.png` / `assignment-active.png` - 作业图标
- `mistake.png` / `mistake-active.png` - 错题本图标
- `profile.png` / `profile-active.png` - 个人中心图标

图标尺寸建议：81px × 81px（tabBar 图标）

## API 接口

### 认证接口

- `POST /auth/wechat/login` - 微信登录
- `POST /auth/wechat/bind` - 绑定手机号
- `POST /auth/sms/send` - 发送验证码

### 用户接口

- `GET /users/me` - 获取当前用户信息
- `PUT /users/me` - 更新个人信息

### 班级接口

- `GET /classes` - 班级列表
- `POST /classes` - 创建班级
- `GET /classes/{id}` - 班级详情

### 题目接口

- `GET /questions` - 题目列表
- `GET /questions/random` - 随机获取题目
- `POST /questions` - 创建题目

### 作业接口

- `GET /assignments` - 作业列表
- `POST /assignments` - 创建作业
- `GET /assignments/{id}` - 作业详情
- `POST /assignments/{id}/submit` - 提交作业

### 刷题记录接口

- `GET /records` - 答题记录
- `POST /records` - 提交答案
- `GET /records/mistakes` - 错题本
- `GET /records/stats` - 统计数据

## 功能模块

### 学生端

- ✅ 微信登录/绑定
- ⏳ 每日刷题
- ⏳ 作业完成
- ⏳ 错题本
- ⏳ 个人统计

### 教师端

- ⏳ 班级管理
- ⏳ 作业管理
- ⏳ 学生统计

## 开发进度

- [x] Task 5: 小程序项目初始化
- [ ] Task 6: 学生端登录和认证
- [ ] Task 7: 学生端每日刷题功能
- [ ] Task 8: 学生端作业完成
- [ ] Task 9: 学生端错题本
- [ ] Task 10: 教师端班级管理
- [ ] Task 11: 教师端作业管理
- [ ] Task 12: 教师端学生统计

## 注意事项

1. **开发环境**：开发者工具中可以关闭域名校验，但正式版必须配置合法域名
2. **HTTPS**：小程序要求所有网络请求必须使用 HTTPS
3. **跨域**：小程序不存在跨域问题，但后端需要配置 CORS
4. **Token 管理**：Token 存储在本地，过期后自动跳转登录页
5. **错误处理**：所有 API 请求都有统一的错误处理

## 调试技巧

1. 使用 `console.log()` 输出调试信息
2. 在开发者工具的 Console 面板查看日志
3. 使用 Network 面板查看网络请求
4. 真机调试可以扫码预览

## 发布流程

1. 在开发者工具中点击"上传"
2. 填写版本号和项目备注
3. 在微信公众平台提交审核
4. 审核通过后发布

## 相关文档

- [微信小程序官方文档](https://developers.weixin.qq.com/miniprogram/dev/framework/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [付刷后端 API 文档](../docs/api-documentation.md)

## 联系方式

如有问题，请联系开发团队。
