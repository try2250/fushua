# 阶段 D 实现文档：三模块打通（进行中）

实施日期：2026-06-10  
状态：🔄 部分完成

## 实施目标

根据 `docs/three-module-platform-handoff-plan.md` 阶段 D 要求，实现三个模块的数据打通和统计联动。

## 已完成的工作

### 1. API 适配层（`app/static/classroom-api.js`）

创建统一的数据访问接口，支持渐进式迁移：

**核心特性：**
- **双模式支持**：可在 localStorage 和 API 之间切换
- **向后兼容**：现有代码无需大规模改动
- **渐进迁移**：通过配置开关逐步启用 API
- **数据迁移**：提供 localStorage 到 API 的迁移工具

**API 方法：**

#### 配置管理
```javascript
ClassroomAPI.useAPI = false;  // 默认使用 localStorage
ClassroomAPI.useAPI = true;   // 切换到 API 模式
```

#### 班级和学生
```javascript
await ClassroomAPI.getClasses()              // 获取班级列表
await ClassroomAPI.getStudents(classId)      // 获取学生列表
```

#### 题库和题目
```javascript
await ClassroomAPI.getQuestionBanks()        // 获取题库列表
await ClassroomAPI.getQuestions(filters)     // 获取题目列表
```

#### 课堂会话
```javascript
await ClassroomAPI.createSession(classId, title, mode)  // 创建会话
await ClassroomAPI.getSession(sessionId)                // 获取会话
await ClassroomAPI.finishSession(sessionId)             // 结束会话
```

#### 抽取记录
```javascript
await ClassroomAPI.createDrawRecord(studentId, questionId, result, scoreDelta, note)
await ClassroomAPI.getDrawRecords(sessionId)
```

#### 数据迁移
```javascript
await ClassroomAPI.migrateFromLocalStorage(classId)     // 迁移历史数据
```

**工作原理：**

```javascript
// 示例：获取班级列表
getClasses: async () => {
    if (!ClassroomAPI.useAPI) {
        // localStorage 模式
        const state = JSON.parse(localStorage.getItem('classroom_companion_data_v2') || '{}');
        return state.classes || [];
    }

    // API 模式
    return await ClassroomAPI.request(`${ClassroomAPI.baseURL}/classes`);
}
```

### 2. 模板集成（`app/templates/teacher/classroom.html`）

在课堂工具页面中引入 API 适配层：

```html
<head>
    <!-- Classroom API Adapter -->
    <script src="/static/classroom-api.js"></script>
    
    <!-- 其他依赖 -->
</head>
```

**使用方式：**
- API 适配层暴露为全局 `window.ClassroomAPI`
- 课堂工具的 React 代码可直接调用
- 通过配置开关控制使用模式

## 待完成的工作

### 1. 前端改造（优先级：高）

需要修改课堂工具的 React 代码，使用 API 适配层：

**当前状态（localStorage）：**
```javascript
// 直接读取 localStorage
const state = JSON.parse(localStorage.getItem('classroom_companion_data_v2') || '{}');
const classes = state.classes || [];
```

**目标状态（API 适配层）：**
```javascript
// 使用 API 适配层
const classes = await ClassroomAPI.getClasses();
```

**改造范围：**
- 班级切换逻辑
- 学生列表加载
- 题目列表加载
- 抽取记录保存
- 课堂会话管理

**改造策略：**
1. 先改造核心流程（创建会话、抽取记录）
2. 保留 localStorage 作为降级方案
3. 添加加载状态和错误处理
4. 提供数据迁移工具界面

### 2. 统计联动（优先级：中）

课堂记录进入系统统计：

**需要实现：**
- 教师统计页面显示课堂数据
- 学生统计页面显示课堂表现
- 题目统计显示课堂使用情况
- 班级统计整合课堂数据

**数据聚合：**
```sql
-- 学生课堂统计
SELECT 
    student_id,
    COUNT(*) as total_draws,
    SUM(CASE WHEN result = 'correct' THEN 1 ELSE 0 END) as correct_count,
    SUM(score_delta) as total_score
FROM classroom_draw_records
WHERE student_id = ?
GROUP BY student_id;

-- 题目课堂统计
SELECT 
    question_id,
    COUNT(*) as used_count,
    AVG(CASE WHEN result = 'correct' THEN 1.0 ELSE 0.0 END) as correct_rate
FROM classroom_draw_records
WHERE question_id IS NOT NULL
GROUP BY question_id;
```

### 3. 前端 UI 增强（优先级：低）

添加用户体验优化：

- **模式切换开关**：页面顶部添加"使用 API 模式"开关
- **数据迁移工具**：提供可视化的数据迁移界面
- **加载状态**：API 请求时显示加载动画
- **错误提示**：网络错误时友好提示
- **离线降级**：API 不可用时自动降级到 localStorage

## 使用指南

### 开发者：启用 API 模式

1. 打开浏览器控制台
2. 执行：
```javascript
ClassroomAPI.useAPI = true;
console.log('API 模式已启用');
```

3. 刷新页面，后续操作将使用 API

### 开发者：迁移历史数据

```javascript
// 假设当前班级 ID 是 1
const result = await ClassroomAPI.migrateFromLocalStorage(1);
console.log('迁移结果:', result);
// 输出: { success: true, session_id: 123, migrated_count: 50, total_count: 50 }
```

### 教师：使用课堂工具

当前阶段教师使用方式不变：
1. 登录系统，点击 "🎓 课堂伴侣"
2. 创建/选择班级
3. 添加学生
4. 开始抽取
5. 查看统计

**未来（启用 API 后）：**
- 数据自动同步到服务器
- 可在不同设备查看课堂记录
- 课堂数据进入学生统计

## 渐进迁移路线

### 第 1 步：引入 API 适配层（✅ 已完成）

- 创建 `classroom-api.js`
- 在模板中引入
- 提供双模式支持

### 第 2 步：核心功能改造（⏳ 待完成）

改造优先级：
1. **课堂会话管理**（最重要）
   - 开始上课时创建会话
   - 结束上课时关闭会话
2. **抽取记录保存**（最重要）
   - 每次抽取保存到 API
   - 自动创建题目快照
3. **班级数据加载**（重要）
   - 从 API 加载班级列表
   - 从 API 加载学生列表
4. **题目数据加载**（可选）
   - 从题库加载题目
   - 支持题目筛选

### 第 3 步：统计联动（⏳ 待完成）

- 教师统计页面显示课堂数据
- 学生统计页面显示课堂表现
- 题目统计显示课堂使用

### 第 4 步：UI 增强（⏳ 待完成）

- 添加模式切换开关
- 添加数据迁移工具
- 优化加载和错误提示

### 第 5 步：全面启用（⏳ 待完成）

- 将 `ClassroomAPI.useAPI` 默认改为 `true`
- 移除 localStorage 降级（可选）
- 完全迁移到 API 模式

## 技术说明

### 为什么使用适配层？

**问题：**
- 课堂工具有 1874 行代码
- 直接改造工作量巨大
- 容易引入 bug

**解决方案：**
- 创建统一的 API 适配层
- 支持 localStorage 和 API 双模式
- 逐步替换，降低风险
- 保持向后兼容

### Token 管理

API 请求需要认证 Token：

```javascript
getToken: () => {
    return localStorage.getItem('auth_token') || '';
}
```

**注意：**
- 确保用户登录后 Token 存储在 `localStorage.auth_token`
- API 请求自动添加 `Authorization` 头
- Token 过期需要重新登录

### 错误处理

API 请求统一错误处理：

```javascript
request: async (url, options = {}) => {
    // ...
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: '网络错误' }));
        throw new Error(error.detail || '请求失败');
    }
    // ...
}
```

**前端需要 catch 错误：**
```javascript
try {
    const classes = await ClassroomAPI.getClasses();
} catch (error) {
    alert('加载失败: ' + error.message);
}
```

## 验收标准

### 阶段 D-1：API 适配层（✅ 已完成）

- [x] 创建 API 适配层文件
- [x] 实现双模式支持
- [x] 提供数据迁移工具
- [x] 在模板中引入

### 阶段 D-2：前端改造（⏳ 待完成）

- [ ] 改造课堂会话管理
- [ ] 改造抽取记录保存
- [ ] 改造班级数据加载
- [ ] 改造学生数据加载
- [ ] 改造题目数据加载
- [ ] 添加加载状态
- [ ] 添加错误处理

### 阶段 D-3：统计联动（⏳ 待完成）

- [ ] 教师统计页面显示课堂数据
- [ ] 学生统计页面显示课堂表现
- [ ] 题目统计显示课堂使用
- [ ] 跨模块数据聚合查询

### 阶段 D-4：UI 增强（⏳ 待完成）

- [ ] 添加模式切换开关
- [ ] 添加数据迁移界面
- [ ] 优化加载动画
- [ ] 优化错误提示

## 下一步工作

立即可以做的：

1. **修改课堂工具 React 代码**
   - 找到 `loadState()` 函数
   - 改为调用 `ClassroomAPI.getClasses()`
   - 找到学生加载逻辑
   - 改为调用 `ClassroomAPI.getStudents()`

2. **添加会话管理**
   - 开始上课时调用 `ClassroomAPI.createSession()`
   - 抽取时调用 `ClassroomAPI.createDrawRecord()`
   - 结束上课时调用 `ClassroomAPI.finishSession()`

3. **添加 UI 控件**
   - 页面顶部添加"启用 API 模式"开关
   - 添加"迁移历史数据"按钮

## 文件清单

### 新增的文件

```
app/static/classroom-api.js              # API 适配层（320 行）
docs/phase-d-three-module-integration.md # 本文档
```

### 修改的文件

```
app/templates/teacher/classroom.html     # 引入 API 适配层
```

## 参考文档

- 主交接文档：`docs/three-module-platform-handoff-plan.md`
- 阶段 A 文档：`docs/phase-a-phone-binding-implementation.md`
- 阶段 B 文档：`docs/phase-b-classroom-web-integration.md`
- 阶段 C 文档：`docs/phase-c-classroom-service.md`
- API 接口：`app/api/v1/classroom.py`

---

**文档版本：** 1.0  
**最后更新：** 2026-06-10  
**实施者：** Claude (Kiro)  
**审核状态：** 进行中
