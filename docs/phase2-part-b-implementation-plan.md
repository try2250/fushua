# Phase 2 Part B: 微信小程序开发实施计划

**开始日期**: 2026-05-18  
**预计完成**: 2026-06-15 (4周)

---

## 一、总体目标

基于已完成的 RESTful API（Part A），开发微信小程序前端，实现学生端和教师端的核心功能。

---

## 二、已完成工作（Part A）

✅ **Task 1**: 班级管理 API (5 tests) - commit b20a8e1  
✅ **Task 2**: 题目管理 API (6 tests) - commit ace8836  
✅ **Task 3**: 作业管理 API (7 tests) - commit f00e535  
✅ **Task 4**: 刷题记录 API (4 tests) - commit 9f8a834

**API 端点总结**:
- `/api/v1/classes` - 班级 CRUD
- `/api/v1/questions` - 题目 CRUD + 随机获取
- `/api/v1/assignments` - 作业 CRUD + 提交
- `/api/v1/records` - 刷题记录 + 错题本 + 统计

---

## 三、Part B 任务分解

### Task 5: 小程序项目初始化 ⏳

**优先级**: P0  
**预计时间**: 4小时

#### 5.1 创建小程序项目结构
```
miniprogram/
├── pages/
│   ├── index/              # 首页（角色选择）
│   ├── login/              # 登录/绑定
│   └── tabbar/             # 底部导航页面
│       ├── practice/       # 刷题（学生）
│       ├── assignments/    # 作业（学生/教师）
│       ├── mistakes/       # 错题本（学生）
│       └── profile/        # 个人中心
├── components/
│   ├── question-card/      # 题目卡片组件
│   └── loading/            # 加载组件
├── utils/
│   ├── request.js          # API 请求封装
│   ├── auth.js             # 认证管理
│   └── storage.js          # 本地存储
├── app.js
├── app.json
├── app.wxss
└── project.config.json
```

#### 5.2 配置文件
- `app.json`: 页面路由、tabBar、窗口配置
- `project.config.json`: 小程序项目配置
- `.env`: API 基础 URL 配置

#### 5.3 工具函数
- `utils/request.js`: 封装 wx.request，自动添加 token
- `utils/auth.js`: 登录状态管理、token 存储
- `utils/storage.js`: 本地存储封装

#### 验收标准
- [ ] 项目结构创建完成
- [ ] 基础配置文件就绪
- [ ] 工具函数可用
- [ ] 可以在微信开发者工具中打开

---

### Task 6: 学生端登录和认证 ⏳

**优先级**: P0  
**预计时间**: 6小时

#### 6.1 微信登录流程
1. 调用 `wx.login()` 获取 code
2. 发送 code 到 `/api/v1/auth/wechat/login`
3. 处理响应：
   - 已注册 → 保存 token，跳转首页
   - 未注册 → 跳转绑定页面

#### 6.2 手机号绑定流程
1. 输入手机号
2. 发送验证码 `/api/v1/auth/sms/send`
3. 输入验证码
4. 选择角色（学生/教师）
5. 学生选择班级，教师输入邀请码
6. 提交绑定 `/api/v1/auth/wechat/bind`
7. 保存 token，跳转首页

#### 6.3 页面开发
- `pages/login/login` - 登录页
- `pages/bind/bind` - 绑定页

#### 验收标准
- [ ] 微信登录流程完整
- [ ] 手机号绑定流程完整
- [ ] Token 正确存储
- [ ] 登录状态持久化
- [ ] 错误提示友好

---

### Task 7: 学生端每日刷题功能 ⏳

**优先级**: P0  
**预计时间**: 8小时

#### 7.1 刷题页面
- 随机获取题目 `GET /api/v1/questions/random`
- 显示题目内容、选项
- 答题交互
- 提交答案 `POST /api/v1/records`
- 显示正确答案和解析
- 下一题按钮

#### 7.2 答题记录
- 答题历史 `GET /api/v1/records`
- 显示答题时间、题目、正误

#### 7.3 统计数据
- 获取统计 `GET /api/v1/records/stats`
- 显示总题数、正确率、今日刷题数

#### 7.4 页面开发
- `pages/tabbar/practice/practice` - 刷题页
- `components/question-card/question-card` - 题目卡片组件

#### 验收标准
- [ ] 可以随机获取题目
- [ ] 答题交互流畅
- [ ] 答案提交成功
- [ ] 显示正确答案和解析
- [ ] 统计数据正确显示

---

### Task 8: 学生端作业完成 ⏳

**优先级**: P0  
**预计时间**: 8小时

#### 8.1 作业列表
- 获取作业列表 `GET /api/v1/assignments`
- 显示作业标题、截止时间、完成状态
- 筛选：全部/未完成/已完成

#### 8.2 作业详情
- 获取作业详情 `GET /api/v1/assignments/{id}`
- 显示作业信息、题目列表
- 答题界面（复用刷题组件）
- 提交作业 `POST /api/v1/assignments/{id}/submit`

#### 8.3 页面开发
- `pages/tabbar/assignments/assignments` - 作业列表
- `pages/assignment-detail/assignment-detail` - 作业详情

#### 验收标准
- [ ] 作业列表正确显示
- [ ] 可以查看作业详情
- [ ] 可以完成作业
- [ ] 提交成功后状态更新
- [ ] 显示作业统计

---

### Task 9: 学生端错题本 ⏳

**优先级**: P1  
**预计时间**: 4小时

#### 9.1 错题列表
- 获取错题 `GET /api/v1/records/mistakes`
- 显示错题列表
- 点击查看题目详情

#### 9.2 错题重做
- 重新答题
- 提交答案
- 更新错题状态

#### 9.3 页面开发
- `pages/tabbar/mistakes/mistakes` - 错题本

#### 验收标准
- [ ] 错题列表正确显示
- [ ] 可以查看错题详情
- [ ] 可以重做错题
- [ ] 错题统计正确

---

### Task 10: 教师端班级管理 ⏳

**优先级**: P1  
**预计时间**: 8小时

#### 10.1 班级列表
- 获取班级列表 `GET /api/v1/classes`
- 显示班级名称、学生数
- 创建班级 `POST /api/v1/classes`

#### 10.2 班级详情
- 获取班级详情 `GET /api/v1/classes/{id}`
- 显示班级信息、成员列表
- 添加成员 `POST /api/v1/classes/{id}/members`
- 移除成员 `DELETE /api/v1/classes/{id}/members/{user_id}`

#### 10.3 页面开发
- `pages/teacher/classes/classes` - 班级列表
- `pages/teacher/class-detail/class-detail` - 班级详情

#### 验收标准
- [ ] 班级列表正确显示
- [ ] 可以创建班级
- [ ] 可以查看班级详情
- [ ] 可以管理班级成员

---

### Task 11: 教师端作业管理 ⏳

**优先级**: P1  
**预计时间**: 8小时

#### 11.1 作业列表
- 获取作业列表 `GET /api/v1/assignments`
- 显示作业标题、班级、截止时间
- 创建作业 `POST /api/v1/assignments`

#### 11.2 作业详情
- 获取作业详情 `GET /api/v1/assignments/{id}`
- 显示作业信息、题目列表
- 查看提交统计 `GET /api/v1/assignments/{id}/stats`

#### 11.3 页面开发
- `pages/teacher/assignments/assignments` - 作业列表
- `pages/teacher/assignment-detail/assignment-detail` - 作业详情
- `pages/teacher/create-assignment/create-assignment` - 创建作业

#### 验收标准
- [ ] 作业列表正确显示
- [ ] 可以创建作业
- [ ] 可以查看作业详情
- [ ] 可以查看提交统计

---

### Task 12: 教师端学生统计 ⏳

**优先级**: P2  
**预计时间**: 6小时

#### 12.1 学生列表
- 获取班级成员 `GET /api/v1/classes/{id}/members`
- 显示学生姓名、刷题数、正确率

#### 12.2 学生详情
- 获取学生统计（需要新增 API）
- 显示学生答题记录、错题统计

#### 12.3 页面开发
- `pages/teacher/students/students` - 学生列表
- `pages/teacher/student-detail/student-detail` - 学生详情

#### 验收标准
- [ ] 学生列表正确显示
- [ ] 可以查看学生详情
- [ ] 统计数据准确

---

## 四、开发时间表

### Week 1 (Day 1-5)
- **Day 1**: Task 5 - 小程序项目初始化
- **Day 2**: Task 6 - 学生端登录和认证
- **Day 3-4**: Task 7 - 学生端每日刷题功能
- **Day 5**: Task 8 - 学生端作业完成（开始）

### Week 2 (Day 6-10)
- **Day 6**: Task 8 - 学生端作业完成（完成）
- **Day 7**: Task 9 - 学生端错题本
- **Day 8-9**: Task 10 - 教师端班级管理
- **Day 10**: Task 11 - 教师端作业管理（开始）

### Week 3 (Day 11-15)
- **Day 11-12**: Task 11 - 教师端作业管理（完成）
- **Day 13-14**: Task 12 - 教师端学生统计
- **Day 15**: 集成测试和 bug 修复

### Week 4 (Day 16-20)
- **Day 16-17**: UI/UX 优化
- **Day 18**: 性能优化
- **Day 19**: 文档编写
- **Day 20**: 发布准备

---

## 五、技术要点

### 5.1 API 请求封装
```javascript
// utils/request.js
const BASE_URL = 'https://your-api.com/api/v1';

function request(url, options = {}) {
  const token = wx.getStorageSync('token');
  return new Promise((resolve, reject) => {
    wx.request({
      url: BASE_URL + url,
      method: options.method || 'GET',
      data: options.data,
      header: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
      },
      success: (res) => {
        if (res.data.code === 0) {
          resolve(res.data.data);
        } else if (res.data.code === 20001 || res.data.code === 20002) {
          // Token 无效，跳转登录
          wx.redirectTo({ url: '/pages/login/login' });
          reject(res.data);
        } else {
          wx.showToast({
            title: res.data.message,
            icon: 'none'
          });
          reject(res.data);
        }
      },
      fail: reject
    });
  });
}
```

### 5.2 认证状态管理
```javascript
// utils/auth.js
function saveToken(token) {
  wx.setStorageSync('token', token);
}

function getToken() {
  return wx.getStorageSync('token');
}

function clearToken() {
  wx.removeStorageSync('token');
}

function isLoggedIn() {
  return !!getToken();
}
```

### 5.3 题目卡片组件
```javascript
// components/question-card/question-card.js
Component({
  properties: {
    question: Object,
    showAnswer: Boolean
  },
  methods: {
    selectOption(e) {
      const option = e.currentTarget.dataset.option;
      this.triggerEvent('select', { option });
    }
  }
});
```

---

## 六、风险和应对

### 6.1 技术风险
- **风险**: 微信小程序 API 限制
- **应对**: 提前阅读文档，了解限制

### 6.2 时间风险
- **风险**: 开发时间超预期
- **应对**: 优先完成核心功能，次要功能后期补充

### 6.3 测试风险
- **风险**: 真机测试问题
- **应对**: 尽早在真机测试，及时发现问题

---

## 七、验收标准

### 7.1 功能完整性
- [ ] 学生端核心功能可用（登录、刷题、作业、错题）
- [ ] 教师端核心功能可用（班级、作业管理）
- [ ] 所有 API 调用正常
- [ ] 错误处理完善

### 7.2 用户体验
- [ ] 界面美观，符合微信设计规范
- [ ] 交互流畅，无卡顿
- [ ] 加载状态明确
- [ ] 错误提示友好

### 7.3 性能指标
- [ ] 首屏加载 < 2s
- [ ] 页面切换流畅
- [ ] 无内存泄漏

---

## 八、后续优化

### 8.1 功能优化
- 消息推送（作业提醒）
- 分享功能（邀请同学）
- 排行榜
- 学习报告

### 8.2 性能优化
- 图片懒加载
- 数据缓存
- 分页加载

### 8.3 体验优化
- 动画效果
- 骨架屏
- 下拉刷新

---

**文档版本**: v1.0  
**最后更新**: 2026-05-18  
**负责人**: 开发团队
