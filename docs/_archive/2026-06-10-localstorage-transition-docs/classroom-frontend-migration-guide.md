# 课堂工具前端改造指南

## 当前状态

✅ **后端 API 已就绪**
- 10 个课堂管理接口完整实现
- 数据库表和迁移已完成
- 权限控制和数据隔离正常

✅ **API 适配层已创建**
- `/static/classroom-api.js` 提供统一接口
- 支持 localStorage 和 API 双模式
- 已在模板中引入

⏳ **前端改造待完成**
- 课堂工具仍使用 localStorage
- 需要修改 React 代码调用 API

## 快速启用指南

### 方式 1：控制台手动启用（测试用）

1. 打开课堂工具页面：`/teacher/classroom`
2. 打开浏览器控制台（F12）
3. 执行以下代码：

```javascript
// 启用 API 模式
ClassroomAPI.useAPI = true;
localStorage.setItem('classroom_api_mode', 'true');
console.log('API 模式已启用');

// 刷新页面后生效
location.reload();
```

4. 之后的操作将自动使用 API

### 方式 2：添加配置面板（推荐）

在课堂工具页面顶部添加配置区域。

**步骤 1：在 `app/templates/teacher/classroom.html` 的 `<body>` 标签后添加：**

```html
<body>
    <!-- API 模式配置面板 -->
    <div id="api-config-panel" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); position: sticky; top: 0; z-index: 1000;">
        <div style="max-width: 1400px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
            <div style="display: flex; align-items: center; gap: 15px;">
                <span style="font-weight: 600; font-size: 14px;">🚀 课堂工具 v2.0</span>
                <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; background: rgba(255,255,255,0.2); padding: 6px 12px; border-radius: 6px; transition: all 0.2s;">
                    <input type="checkbox" id="apiModeToggle" style="width: 16px; height: 16px; cursor: pointer;" onchange="window.toggleAPIMode(this.checked)">
                    <span style="font-size: 13px;">启用 API 模式（服务器同步）</span>
                </label>
                <span id="apiModeStatus" style="font-size: 12px; opacity: 0.9;"></span>
            </div>
            <div style="display: flex; gap: 10px;">
                <button onclick="window.showMigrationDialog()" style="background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); color: white; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 13px; transition: all 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.3)'" onmouseout="this.style.background='rgba(255,255,255,0.2)'">
                    📦 迁移历史数据
                </button>
                <button onclick="window.showAPIGuide()" style="background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); color: white; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 13px; transition: all 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.3)'" onmouseout="this.style.background='rgba(255,255,255,0.2)'">
                    ❓ 使用说明
                </button>
            </div>
        </div>
    </div>

    <div id="root"></div>
```

**步骤 2：在 React 代码之前（第 77 行附近）添加全局函数：**

```html
<script>
    // === API 模式管理全局函数 ===
    
    window.toggleAPIMode = function(enabled) {
        ClassroomAPI.useAPI = enabled;
        localStorage.setItem('classroom_api_mode', enabled ? 'true' : 'false');
        
        const status = document.getElementById('apiModeStatus');
        if (enabled) {
            status.textContent = '✓ 数据将同步到服务器';
            status.style.color = '#4ade80';
        } else {
            status.textContent = '⚠ 仅保存在浏览器本地';
            status.style.color = '#fbbf24';
        }
        
        // 提示用户刷新
        if (confirm(enabled ? 
            'API 模式已启用！\n\n数据将同步到服务器，支持多设备访问。\n点击"确定"刷新页面使其生效。' : 
            'API 模式已关闭！\n\n数据仅保存在浏览器本地。\n点击"确定"刷新页面使其生效。'
        )) {
            location.reload();
        }
    };
    
    window.showMigrationDialog = async function() {
        if (!ClassroomAPI.useAPI) {
            alert('请先启用 API 模式后再迁移数据');
            return;
        }
        
        const classId = prompt('请输入要迁移的班级 ID:\n\n提示：可在班级管理页面查看班级 ID');
        if (!classId) return;
        
        const confirmed = confirm(
            `确认迁移班级 ${classId} 的历史数据？\n\n` +
            '这将把浏览器本地的抽取记录同步到服务器。\n' +
            '迁移过程可能需要几秒钟，请耐心等待。'
        );
        
        if (!confirmed) return;
        
        try {
            const btn = event.target;
            btn.disabled = true;
            btn.textContent = '⏳ 迁移中...';
            
            const result = await ClassroomAPI.migrateFromLocalStorage(parseInt(classId));
            
            btn.disabled = false;
            btn.textContent = '📦 迁移历史数据';
            
            alert(
                `✅ 迁移成功！\n\n` +
                `共迁移 ${result.migrated_count}/${result.total_count} 条记录\n` +
                `会话 ID: ${result.session_id}`
            );
        } catch (error) {
            alert('❌ 迁移失败：' + error.message);
            event.target.disabled = false;
            event.target.textContent = '📦 迁移历史数据';
        }
    };
    
    window.showAPIGuide = function() {
        const guide = `
📖 API 模式使用说明

【什么是 API 模式？】
• localStorage 模式：数据保存在浏览器本地，仅当前设备可用
• API 模式：数据保存在服务器，支持多设备同步访问

【如何启用？】
1. 勾选"启用 API 模式"复选框
2. 刷新页面使其生效
3. 之后的所有操作将自动同步到服务器

【如何迁移历史数据？】
1. 先启用 API 模式
2. 点击"迁移历史数据"按钮
3. 输入班级 ID
4. 等待迁移完成

【注意事项】
⚠ 启用 API 模式后，需要保持网络连接
⚠ API 模式下数据操作较慢，但更安全可靠
⚠ 建议先迁移历史数据，再开始使用 API 模式

【当前状态】
模式：${ClassroomAPI.useAPI ? 'API 模式' : 'localStorage 模式'}
版本：v2.0
        `.trim();
        
        alert(guide);
    };
    
    // === 页面加载时初始化 ===
    window.addEventListener('DOMContentLoaded', function() {
        // 恢复上次的设置
        const savedMode = localStorage.getItem('classroom_api_mode') === 'true';
        ClassroomAPI.useAPI = savedMode;
        
        const toggle = document.getElementById('apiModeToggle');
        const status = document.getElementById('apiModeStatus');
        
        if (toggle) {
            toggle.checked = savedMode;
            
            if (savedMode) {
                status.textContent = '✓ 数据将同步到服务器';
                status.style.color = '#4ade80';
            } else {
                status.textContent = '⚠ 仅保存在浏览器本地';
                status.style.color = '#fbbf24';
            }
        }
        
        // 首次使用提示
        const hasSeenGuide = localStorage.getItem('classroom_api_guide_seen');
        if (!hasSeenGuide) {
            setTimeout(() => {
                if (confirm(
                    '👋 欢迎使用课堂工具 v2.0！\n\n' +
                    '新版本支持数据同步到服务器。\n' +
                    '是否查看使用说明？'
                )) {
                    window.showAPIGuide();
                }
                localStorage.setItem('classroom_api_guide_seen', 'true');
            }, 1000);
        }
    });
</script>
```

**步骤 3：验证**

1. 刷新课堂工具页面
2. 看到顶部紫色配置栏
3. 勾选"启用 API 模式"
4. 刷新页面
5. 使用课堂工具，数据将自动同步到服务器

## 数据流说明

### localStorage 模式（默认）

```
用户操作 → React State → localStorage
         ↓
     页面刷新
         ↓
  从 localStorage 恢复
```

### API 模式（启用后）

```
用户操作 → React State → ClassroomAPI.xxx()
         ↓              ↓
     页面刷新      后端数据库
         ↓              ↓
  从 API 加载 ← 服务器
```

## 完整改造方案（未来）

如果需要完全重构前端，建议：

### 方案 A：渐进式改造（推荐）

**第 1 周：核心数据加载**
```javascript
// 修改 loadState 函数
const loadState = async () => {
    if (ClassroomAPI.useAPI) {
        try {
            const classes = await ClassroomAPI.getClasses();
            // 转换为本地格式
            return {
                classes: classes.map(c => ({
                    id: c.id,
                    name: c.name
                })),
                activeClassId: classes[0]?.id || null,
                students: [],
                questions: []
            };
        } catch (error) {
            console.error('加载失败，使用本地数据', error);
            // 降级到 localStorage
        }
    }
    
    // 原有 localStorage 逻辑
    const s = localStorage.getItem(STORAGE_KEY);
    // ...
};
```

**第 2 周：学生和题目加载**
```javascript
// 在切换班级时加载学生
const handleClassChange = async (classId) => {
    if (ClassroomAPI.useAPI) {
        const students = await ClassroomAPI.getStudents(classId);
        updateStudents(students);
    }
};
```

**第 3 周：会话和抽取记录**
```javascript
// 开始上课时创建会话
const startSession = async () => {
    if (ClassroomAPI.useAPI) {
        const session = await ClassroomAPI.createSession(
            activeClassId,
            `数学课 ${new Date().toLocaleDateString()}`,
            'normal'
        );
        // 保存 session.id
    }
};

// 抽取时保存记录
const onDrawStudent = async (student, question, result) => {
    if (ClassroomAPI.useAPI) {
        await ClassroomAPI.createDrawRecord(
            student.id,
            question?.id,
            result,
            10,
            ''
        );
    }
    // 原有逻辑
};
```

### 方案 B：完全重构（长期）

使用现代化工具链：
- React + TypeScript
- Vite 构建
- React Query 数据管理
- Tailwind CSS
- 完全 API 驱动

## 测试检查清单

启用 API 模式后，测试以下功能：

- [ ] 页面正常加载
- [ ] 配置面板显示正确
- [ ] 切换 API 模式后刷新生效
- [ ] 创建班级（如果接入 API）
- [ ] 加载学生列表（如果接入 API）
- [ ] 开始课堂会话（如果接入 API）
- [ ] 抽取学生并记录（如果接入 API）
- [ ] 查看统计数据
- [ ] 数据迁移功能
- [ ] 错误处理和提示

## 故障排查

### 问题 1：配置面板不显示

检查：
```javascript
// 浏览器控制台
console.log(typeof ClassroomAPI); // 应该是 'object'
```

解决：确保 `/static/classroom-api.js` 正确加载

### 问题 2：API 请求失败

检查：
```javascript
// 浏览器控制台
console.log(ClassroomAPI.getToken()); // 应该返回 token
```

解决：确保用户已登录，token 存储在 localStorage

### 问题 3：数据不同步

检查：
```javascript
// 浏览器控制台
console.log(ClassroomAPI.useAPI); // 应该是 true
console.log(localStorage.getItem('classroom_api_mode')); // 应该是 'true'
```

解决：重新启用 API 模式并刷新

## 总结

当前实施方案：

✅ **已完成**
- API 适配层完整实现
- 配置面板 UI 代码已提供
- 使用指南和故障排查文档

📝 **下一步**
- 将配置面板代码添加到 `classroom.html`
- 测试 API 模式开关
- 逐步改造核心功能
- 完善错误处理

🎯 **目标**
- 用户可以轻松启用 API 模式
- 数据自动同步到服务器
- 支持多设备访问
- 保持向后兼容
