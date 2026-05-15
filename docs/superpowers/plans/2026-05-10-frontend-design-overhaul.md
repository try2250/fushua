# 付刷前端界面优化 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将付刷从功能性界面升级为视觉精致、交互流畅的教育产品级界面，采用"学术雅致"设计语言——深蓝墨色为主调、暖金为点缀、衬线字体为标题，营造沉稳专注的学习氛围。

**Architecture:** 纯 CSS 重构（不引入前端框架），通过 CSS 变量系统化改造配色/字体/间距/动效，逐页面优化模板结构。保持 Jinja2 + htmx 技术栈不变。

**Tech Stack:** CSS3 (Custom Properties, Grid, Flexbox, Animations), Jinja2, htmx, KaTeX

---

## 设计方向：学术雅致 (Scholarly Refinement)

**核心美学：**
- **色彩**：深蓝墨 (#0f172a) + 暖金 (#d4a853) + 象牙白 (#faf8f5)，远离通用蓝紫渐变
- **字体**：标题用 Noto Serif SC（衬线），正文用 Noto Sans SC（无衬线），代码用 JetBrains Mono
- **空间**：大呼吸感，卡片间留白充足，内容不拥挤
- **动效**：克制的微交互——卡片入场、按钮涟漪、导航高亮滑动，不做过度动画
- **纹理**：微妙纸张质感背景，卡片有轻微阴影层次感

---

## 文件结构

| 操作 | 文件路径 | 职责 |
|------|----------|------|
| 重写 | `app/static/style.css` | 全新设计系统 |
| 修改 | `app/templates/base.html` | 导航栏重构、字体加载 |
| 修改 | `app/templates/login.html` | 登录页视觉升级 |
| 修改 | `app/templates/register.html` | 注册页视觉升级 |
| 修改 | `app/templates/recover.html` | 找回页视觉升级 |
| 修改 | `app/templates/recover_submitted.html` | 找回成功页视觉升级 |
| 修改 | `app/templates/admin/index.html` | 管理后台首页升级 |
| 修改 | `app/templates/admin/users.html` | 用户管理页升级 |
| 修改 | `app/templates/admin/classes.html` | 班级管理页升级 |
| 修改 | `app/templates/admin/invite.html` | 邀请码管理页升级 |
| 修改 | `app/templates/admin/recovery_requests.html` | 找回申请页升级 |
| 修改 | `app/templates/student/dashboard.html` | 学生仪表盘升级 |
| 修改 | `app/templates/index.html` | 首页升级 |

---

### Task 1: CSS 设计系统重构

**Files:**
- Rewrite: `app/static/style.css`
- Modify: `app/templates/base.html`

- [ ] **Step 1: 重写 style.css — 全新设计系统**

将 `app/static/style.css` 完整替换为以下内容。这是整个前端优化的核心，定义了所有设计令牌和组件样式：

```css
:root {
    --ink: #0f172a;
    --ink-light: #334155;
    --ink-muted: #64748b;
    --gold: #d4a853;
    --gold-light: #e8cc8c;
    --gold-bg: rgba(212, 168, 83, 0.08);
    --ivory: #faf8f5;
    --ivory-dark: #f0ede6;
    --paper: #ffffff;
    --paper-shadow: 0 1px 3px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.04);
    --paper-shadow-hover: 0 4px 12px rgba(15, 23, 42, 0.08), 0 2px 4px rgba(15, 23, 42, 0.04);
    --paper-shadow-elevated: 0 8px 24px rgba(15, 23, 42, 0.1), 0 4px 8px rgba(15, 23, 42, 0.06);
    --success: #16a34a;
    --success-bg: #f0fdf4;
    --danger: #dc2626;
    --danger-bg: #fef2f2;
    --warning: #d97706;
    --warning-bg: #fffbeb;
    --info: #2563eb;
    --info-bg: #eff6ff;
    --radius-sm: 6px;
    --radius: 10px;
    --radius-lg: 14px;
    --radius-xl: 20px;
    --font-display: "Noto Serif SC", "Source Han Serif SC", Georgia, serif;
    --font-body: "Noto Sans SC", -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    --font-mono: "JetBrains Mono", "Fira Code", "Cascadia Code", monospace;
    --transition: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    --transition-slow: 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

[data-theme="dark"] {
    --ink: #e2e8f0;
    --ink-light: #cbd5e1;
    --ink-muted: #94a3b8;
    --ivory: #0f172a;
    --ivory-dark: #1e293b;
    --paper: #1e293b;
    --paper-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
    --paper-shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.3);
    --paper-shadow-elevated: 0 8px 24px rgba(0, 0, 0, 0.4);
    --success-bg: #052e16;
    --danger-bg: #450a0a;
    --warning-bg: #451a03;
    --info-bg: #172554;
    --gold-bg: rgba(212, 168, 83, 0.12);
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: var(--font-body);
    background: var(--ivory);
    color: var(--ink);
    line-height: 1.7;
    -webkit-font-smoothing: antialiased;
}

::selection {
    background: var(--gold);
    color: var(--ivory);
}

.navbar {
    background: var(--ink);
    color: white;
    padding: 0;
    position: sticky;
    top: 0;
    z-index: 100;
    border-bottom: 2px solid var(--gold);
}

[data-theme="dark"] .navbar {
    background: #0c1222;
}

.nav-container {
    max-width: 960px;
    margin: 0 auto;
    padding: 0 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 56px;
}

.logo {
    color: white;
    text-decoration: none;
    font-family: var(--font-display);
    font-size: 1.35rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}

.nav-links {
    display: flex;
    align-items: center;
    gap: 0.15rem;
    flex-wrap: wrap;
}

.nav-link {
    color: rgba(255, 255, 255, 0.7);
    text-decoration: none;
    padding: 0.35rem 0.65rem;
    border-radius: var(--radius-sm);
    font-size: 0.85rem;
    transition: var(--transition);
    white-space: nowrap;
}

.nav-link:hover {
    background: rgba(255, 255, 255, 0.08);
    color: white;
}

.nav-link-logout {
    color: rgba(255, 255, 255, 0.5);
}

.nav-user {
    color: var(--gold-light);
    font-size: 0.82rem;
    margin-right: 0.4rem;
    font-weight: 500;
}

.container {
    max-width: 960px;
    margin: 0 auto;
    padding: 0 1.5rem;
}

main.container {
    padding-top: 2rem;
    padding-bottom: 3rem;
}

h1 {
    font-family: var(--font-display);
    font-size: 1.65rem;
    color: var(--ink);
    margin-bottom: 1.5rem;
    font-weight: 700;
    letter-spacing: 0.01em;
}

h2 {
    font-family: var(--font-display);
    font-size: 1.15rem;
    color: var(--ink-light);
    margin-bottom: 1rem;
    font-weight: 600;
}

.card {
    background: var(--paper);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    margin-bottom: 1.2rem;
    box-shadow: var(--paper-shadow);
    border: 1px solid rgba(15, 23, 42, 0.04);
    transition: var(--transition);
    animation: cardIn 0.4s ease-out both;
}

[data-theme="dark"] .card {
    border-color: rgba(255, 255, 255, 0.06);
}

@keyframes cardIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

.form-group {
    margin-bottom: 1.1rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.4rem;
    font-weight: 600;
    color: var(--ink-light);
    font-size: 0.88rem;
    letter-spacing: 0.01em;
}

.form-group input,
.form-group textarea,
.form-group select {
    width: 100%;
    padding: 0.65rem 0.9rem;
    border: 1.5px solid var(--ivory-dark);
    border-radius: var(--radius);
    font-size: 0.95rem;
    font-family: var(--font-body);
    transition: var(--transition);
    background: var(--paper);
    color: var(--ink);
}

[data-theme="dark"] .form-group input,
[data-theme="dark"] .form-group textarea,
[data-theme="dark"] .form-group select {
    border-color: rgba(255, 255, 255, 0.1);
    background: var(--ivory-dark);
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
    outline: none;
    border-color: var(--gold);
    box-shadow: 0 0 0 3px var(--gold-bg);
}

.form-row {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 1rem;
}

.form-row-2col {
    grid-template-columns: 1fr 1fr;
}

.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.4rem;
    padding: 0.6rem 1.2rem;
    background: var(--ink);
    color: white;
    border: none;
    border-radius: var(--radius);
    font-size: 0.9rem;
    font-family: var(--font-body);
    font-weight: 500;
    cursor: pointer;
    transition: var(--transition);
    text-decoration: none;
    text-align: center;
    position: relative;
    overflow: hidden;
}

.btn:hover {
    background: var(--ink-light);
    transform: translateY(-1px);
    box-shadow: var(--paper-shadow-hover);
}

.btn:active {
    transform: translateY(0);
}

.btn-primary {
    background: var(--gold);
    color: var(--ink);
    font-weight: 600;
}

.btn-primary:hover {
    background: var(--gold-light);
}

.btn-outline {
    background: transparent;
    color: var(--ink);
    border: 1.5px solid var(--ivory-dark);
}

[data-theme="dark"] .btn-outline {
    border-color: rgba(255, 255, 255, 0.15);
    color: var(--ink-light);
}

.btn-outline:hover {
    border-color: var(--gold);
    color: var(--gold);
    background: var(--gold-bg);
}

.btn-danger {
    background: var(--danger);
}

.btn-danger:hover {
    background: #b91c1c;
}

.btn-sm {
    padding: 0.3rem 0.7rem;
    font-size: 0.8rem;
    border-radius: var(--radius-sm);
}

.btn-lg {
    padding: 0.75rem 2rem;
    font-size: 1rem;
    border-radius: var(--radius-lg);
}

.btn-block {
    display: flex;
    width: 100%;
}

.stats-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 0.8rem;
    margin-bottom: 1.5rem;
}

.stat-card {
    background: var(--paper);
    border-radius: var(--radius-lg);
    padding: 1.2rem 1rem;
    text-align: center;
    box-shadow: var(--paper-shadow);
    border: 1px solid rgba(15, 23, 42, 0.04);
    transition: var(--transition);
}

[data-theme="dark"] .stat-card {
    border-color: rgba(255, 255, 255, 0.06);
}

.stat-card:hover {
    box-shadow: var(--paper-shadow-hover);
    transform: translateY(-2px);
}

.stat-number {
    font-family: var(--font-display);
    font-size: 1.9rem;
    font-weight: 700;
    color: var(--ink);
    line-height: 1.2;
}

.stat-label {
    color: var(--ink-muted);
    font-size: 0.82rem;
    margin-top: 0.3rem;
    letter-spacing: 0.02em;
}

.stat-correct .stat-number { color: var(--success); }
.stat-wrong .stat-number { color: var(--danger); }

.badge {
    display: inline-flex;
    align-items: center;
    padding: 0.15rem 0.55rem;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}

.badge-subject { background: var(--info-bg); color: var(--info); }
.badge-chapter { background: var(--ivory-dark); color: var(--ink-muted); }
.badge-semester { background: #ecfdf5; color: #047857; }
.badge-custom { background: #faf5ff; color: #7c3aed; }
.badge-correct, .badge-success { background: var(--success-bg); color: var(--success); }
.badge-wrong { background: var(--danger-bg); color: var(--danger); }

.badge-diff-1 { background: var(--success-bg); color: var(--success); }
.badge-diff-2 { background: var(--warning-bg); color: var(--warning); }
.badge-diff-3 { background: var(--danger-bg); color: var(--danger); }

.badge-type-choice { background: var(--info-bg); color: var(--info); }
.badge-type-multi_choice { background: #faf5ff; color: #7c3aed; }
.badge-type-fill { background: var(--warning-bg); color: var(--warning); }
.badge-type-judge { background: var(--danger-bg); color: var(--danger); }

.auth-card {
    max-width: 440px;
    margin: 3rem auto;
    background: var(--paper);
    border-radius: var(--radius-xl);
    padding: 2.5rem 2rem;
    box-shadow: var(--paper-shadow-elevated);
    border: 1px solid rgba(15, 23, 42, 0.04);
}

[data-theme="dark"] .auth-card {
    border-color: rgba(255, 255, 255, 0.06);
}

.auth-card h1 {
    font-family: var(--font-display);
    text-align: center;
    margin-bottom: 1.8rem;
    font-size: 1.5rem;
}

.auth-switch {
    text-align: center;
    margin-top: 1.5rem;
    color: var(--ink-muted);
    font-size: 0.88rem;
}

.auth-switch a {
    color: var(--gold);
    text-decoration: none;
    font-weight: 500;
}

.auth-switch a:hover {
    text-decoration: underline;
}

.alert {
    padding: 0.75rem 1rem;
    border-radius: var(--radius);
    margin-bottom: 1rem;
    font-size: 0.88rem;
    border: 1px solid transparent;
}

.alert-error {
    background: var(--danger-bg);
    color: var(--danger);
    border-color: rgba(220, 38, 38, 0.15);
}

.alert-success {
    background: var(--success-bg);
    color: var(--success);
    border-color: rgba(22, 163, 74, 0.15);
}

.alert-weak {
    border: 2px solid var(--warning);
    background: var(--warning-bg);
}

.data-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 0.88rem;
}

.data-table th {
    background: var(--ivory-dark);
    padding: 0.75rem 0.8rem;
    text-align: left;
    font-weight: 600;
    color: var(--ink-muted);
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    border-bottom: 2px solid rgba(15, 23, 42, 0.06);
}

.data-table td {
    padding: 0.75rem 0.8rem;
    border-bottom: 1px solid rgba(15, 23, 42, 0.04);
    color: var(--ink-light);
}

[data-theme="dark"] .data-table th {
    background: var(--ivory-dark);
    border-bottom-color: rgba(255, 255, 255, 0.08);
}

[data-theme="dark"] .data-table td {
    border-bottom-color: rgba(255, 255, 255, 0.04);
}

.data-table tr:hover td {
    background: var(--gold-bg);
}

.hero {
    text-align: center;
    padding: 2.5rem 0 1.5rem;
}

.hero h1 {
    font-family: var(--font-display);
    font-size: 2.4rem;
    color: var(--ink);
    margin-bottom: 0.6rem;
    font-weight: 700;
}

.hero-sub {
    color: var(--ink-muted);
    font-size: 1.05rem;
    line-height: 1.6;
}

.welcome-actions {
    display: flex;
    gap: 1rem;
    justify-content: center;
    flex-wrap: wrap;
    margin-top: 1.5rem;
}

.subject-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
    gap: 0.8rem;
}

.subject-card {
    display: block;
    background: var(--paper);
    border: 1.5px solid rgba(15, 23, 42, 0.06);
    border-radius: var(--radius-lg);
    padding: 1.1rem 0.8rem;
    text-align: center;
    text-decoration: none;
    color: var(--ink);
    transition: var(--transition);
    box-shadow: var(--paper-shadow);
}

.subject-card:hover {
    border-color: var(--gold);
    transform: translateY(-3px);
    box-shadow: var(--paper-shadow-hover);
}

.subject-name {
    font-family: var(--font-display);
    font-weight: 600;
    font-size: 1rem;
}

.subject-count {
    color: var(--ink-muted);
    font-size: 0.78rem;
    margin-top: 0.3rem;
}

.question-card {
    border-left: 4px solid var(--gold);
}

.question-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.8rem;
}

.question-number {
    font-weight: 600;
    color: var(--ink);
    font-size: 0.9rem;
}

.question-content {
    font-size: 1.02rem;
    margin-bottom: 1rem;
    line-height: 1.8;
    white-space: pre-wrap;
}

.question-content .katex { font-size: 1.1em; }
.question-content .katex-display { margin: 0.8rem 0; overflow-x: auto; }

.question-image {
    margin-bottom: 0.8rem;
    text-align: center;
}

.question-image img {
    max-width: 100%;
    max-height: 300px;
    border-radius: var(--radius);
    border: 1px solid rgba(15, 23, 42, 0.06);
}

.options-group {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
}

.option-label {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    padding: 0.75rem 1rem;
    border: 1.5px solid rgba(15, 23, 42, 0.08);
    border-radius: var(--radius);
    cursor: pointer;
    transition: var(--transition);
}

.option-label:hover {
    border-color: var(--gold);
    background: var(--gold-bg);
}

.option-label input[type="radio"] {
    margin-top: 0.25rem;
    accent-color: var(--gold);
}

.option-label input[type="radio"]:checked + .option-text {
    color: var(--gold);
    font-weight: 500;
}

.option-label:has(input:checked) {
    border-color: var(--gold);
    background: var(--gold-bg);
}

.option-text {
    font-size: 0.95rem;
}

.submit-bar {
    position: sticky;
    bottom: 0;
    background: var(--paper);
    padding: 1rem 1.5rem;
    border-radius: var(--radius-lg);
    box-shadow: 0 -2px 12px rgba(15, 23, 42, 0.08);
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 1rem;
}

.submit-info {
    color: var(--ink-muted);
    font-size: 0.88rem;
}

.result-card { border-left: 4px solid var(--ink-muted); }
.result-correct { border-left-color: var(--success); }
.result-wrong { border-left-color: var(--danger); }

.result-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
}

.result-detail {
    margin-top: 0.8rem;
    display: flex;
    gap: 1.5rem;
    font-size: 0.9rem;
}

.correct-answer { color: var(--success); }

.result-explanation {
    margin-top: 0.8rem;
    padding: 0.9rem 1rem;
    background: var(--gold-bg);
    border-radius: var(--radius);
    font-size: 0.9rem;
    color: var(--ink-light);
    line-height: 1.7;
    border-left: 3px solid var(--gold);
}

.question-list {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
}

.question-item {
    padding: 1rem 0;
    border-bottom: 1px solid rgba(15, 23, 42, 0.04);
}

.question-item:last-child { border-bottom: none; }

.question-meta {
    display: flex;
    gap: 0.4rem;
    margin-bottom: 0.5rem;
}

.question-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 0.5rem;
}

.question-answer {
    color: var(--success);
    font-size: 0.85rem;
    font-weight: 500;
}

.flex-between {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.filter-group {
    display: flex;
    gap: 0.4rem;
    flex-wrap: wrap;
}

.record-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.8rem 0;
    border-bottom: 1px solid rgba(15, 23, 42, 0.04);
}

.record-item:last-child { border-bottom: none; }

.record-correct { border-left: 3px solid var(--success); padding-left: 0.8rem; }
.record-wrong { border-left: 3px solid var(--danger); padding-left: 0.8rem; }

.record-info {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.record-content { font-size: 0.9rem; color: var(--ink-light); }

.record-result {
    display: flex;
    align-items: center;
    gap: 0.8rem;
}

.record-result small { color: var(--ink-muted); }

.role-select {
    display: flex;
    gap: 1rem;
}

.feature-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
}

.feature-item {
    text-align: center;
    padding: 1.3rem 0.8rem;
    border-radius: var(--radius-lg);
    background: var(--gold-bg);
}

.feature-icon { font-size: 2rem; margin-bottom: 0.5rem; }

.feature-title {
    font-family: var(--font-display);
    font-weight: 600;
    color: var(--ink);
    margin-bottom: 0.3rem;
}

.feature-desc { color: var(--ink-muted); font-size: 0.85rem; }

.empty {
    color: var(--ink-muted);
    text-align: center;
    padding: 2.5rem 0;
    font-size: 0.95rem;
}

.fill-input {
    width: 100%;
    padding: 0.7rem 1rem;
    border: 2px dashed rgba(15, 23, 42, 0.12);
    border-radius: var(--radius);
    font-size: 1rem;
    font-family: var(--font-body);
    transition: var(--transition);
    background: var(--paper);
    color: var(--ink);
}

.fill-input:focus {
    outline: none;
    border-color: var(--gold);
    border-style: solid;
    box-shadow: 0 0 0 3px var(--gold-bg);
}

.mistake-card { border-left: 4px solid var(--danger); }
.mistake-mastered { border-left-color: var(--success); opacity: 0.75; }

.mistake-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
}

.mistake-detail {
    display: flex;
    gap: 1.5rem;
    margin-top: 0.5rem;
    font-size: 0.9rem;
}

.wrong-answer { color: var(--danger); }

.mistake-time { margin-top: 0.5rem; color: var(--ink-muted); }

.weak-section { margin-top: 1rem; }
.weak-section h3 { font-size: 0.95rem; color: var(--warning); margin-bottom: 0.5rem; }

.weak-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.weak-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.7rem 1rem;
    background: var(--paper);
    border-radius: var(--radius);
    text-decoration: none;
    color: var(--ink);
    transition: var(--transition);
    border: 1px solid rgba(15, 23, 42, 0.06);
}

.weak-item:hover {
    border-color: var(--gold);
    transform: translateX(4px);
}

.weak-name { flex: 1; font-weight: 500; }
.weak-accuracy { color: var(--danger); font-weight: bold; font-size: 1.1rem; }
.weak-action { color: var(--gold); font-size: 0.85rem; }

.bar-chart {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
}

.bar-row {
    display: flex;
    align-items: center;
    gap: 0.8rem;
}

.bar-label {
    width: 80px;
    text-align: right;
    font-size: 0.88rem;
    color: var(--ink-muted);
    flex-shrink: 0;
}

.bar-track {
    flex: 1;
    height: 24px;
    background: var(--ivory-dark);
    border-radius: 12px;
    overflow: hidden;
}

.bar-fill {
    height: 100%;
    border-radius: 12px;
    transition: width 0.5s ease;
    min-width: 2px;
}

.bar-good { background: linear-gradient(90deg, var(--success), #22c55e); }
.bar-warning { background: linear-gradient(90deg, var(--warning), #f59e0b); }
.bar-danger { background: linear-gradient(90deg, var(--danger), #ef4444); }

.bar-value {
    width: 50px;
    text-align: right;
    font-weight: bold;
    font-size: 0.88rem;
    color: var(--ink);
}

.bar-detail {
    width: 50px;
    text-align: right;
    font-size: 0.8rem;
    color: var(--ink-muted);
}

.stats-row-4 { grid-template-columns: repeat(4, 1fr); }

.filter-divider { color: rgba(15, 23, 42, 0.12); margin: 0 0.3rem; }

.accuracy-badge {
    display: inline-block;
    padding: 0.2rem 0.5rem;
    border-radius: 10px;
    font-size: 0.8rem;
    font-weight: 600;
}

.multi-hint {
    color: #7c3aed;
    font-size: 0.85rem;
    margin-bottom: 0.5rem;
    font-weight: 500;
}

.multi-answer-group {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
}

.multi-answer-label {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.5rem 1rem;
    border: 2px solid rgba(15, 23, 42, 0.08);
    border-radius: var(--radius);
    cursor: pointer;
    font-weight: 500;
    transition: var(--transition);
}

.multi-answer-label:has(input:checked) {
    border-color: #7c3aed;
    background: #faf5ff;
    color: #7c3aed;
}

.multi-answer-label input { accent-color: #7c3aed; }

.btn-group { display: flex; gap: 0.5rem; }

.file-input {
    padding: 0.8rem;
    border: 2px dashed rgba(15, 23, 42, 0.12);
    border-radius: var(--radius);
    width: 100%;
    background: var(--ivory-dark);
    cursor: pointer;
    transition: var(--transition);
}

.file-input:hover { border-color: var(--gold); }

.format-example {
    background: var(--ink);
    color: var(--gold-light);
    padding: 1rem 1.2rem;
    border-radius: var(--radius);
    font-family: var(--font-mono);
    font-size: 0.82rem;
    overflow-x: auto;
    line-height: 1.5;
    white-space: pre;
}

.format-hint { color: var(--ink-muted); font-size: 0.85rem; margin-bottom: 0.5rem; }

.trend-chart {
    display: flex;
    align-items: flex-end;
    gap: 4px;
    height: 160px;
    padding: 0.5rem 0;
    overflow-x: auto;
}

.trend-day {
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 36px;
    flex: 1;
}

.trend-bar-wrap {
    flex: 1;
    display: flex;
    align-items: flex-end;
    width: 100%;
}

.trend-bar {
    width: 100%;
    max-width: 28px;
    background: linear-gradient(180deg, var(--gold), var(--gold-light));
    border-radius: 4px 4px 0 0;
    min-height: 4px;
}

.trend-label { font-size: 0.7rem; color: var(--ink-muted); margin-top: 4px; }
.trend-count { font-size: 0.7rem; color: var(--gold); font-weight: 600; }

.quick-actions {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.8rem;
}

.action-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 1.1rem 0.5rem;
    background: var(--gold-bg);
    border-radius: var(--radius-lg);
    text-decoration: none;
    color: var(--ink);
    transition: var(--transition);
    position: relative;
    border: 1px solid transparent;
}

.action-card:hover {
    background: var(--paper);
    border-color: var(--gold);
    transform: translateY(-2px);
    box-shadow: var(--paper-shadow-hover);
}

.action-icon { font-size: 1.8rem; margin-bottom: 0.3rem; }
.action-text { font-size: 0.85rem; font-weight: 500; }

.action-badge {
    position: absolute;
    top: 4px;
    right: 8px;
    background: var(--danger);
    color: white;
    font-size: 0.7rem;
    padding: 0.1rem 0.4rem;
    border-radius: 8px;
    font-weight: 600;
}

.breadcrumb {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    margin-bottom: 1.2rem;
    font-size: 0.88rem;
    flex-wrap: wrap;
}

.breadcrumb-item {
    color: var(--gold);
    text-decoration: none;
    padding: 0.2rem 0.4rem;
    border-radius: var(--radius-sm);
    transition: var(--transition);
}

.breadcrumb-item:hover { background: var(--gold-bg); }
.breadcrumb-item.active { color: var(--ink); font-weight: 600; cursor: default; }
.breadcrumb-item.active:hover { background: transparent; }
.breadcrumb-sep { color: var(--ink-muted); font-size: 1rem; }

.semester-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 0.8rem;
}

.semester-card {
    display: block;
    background: var(--paper);
    border: 1.5px solid rgba(15, 23, 42, 0.06);
    border-radius: var(--radius-lg);
    padding: 1rem 0.8rem;
    text-align: center;
    text-decoration: none;
    color: var(--ink);
    transition: var(--transition);
    box-shadow: var(--paper-shadow);
}

.semester-card:hover {
    border-color: var(--gold);
    transform: translateY(-2px);
    box-shadow: var(--paper-shadow-hover);
}

.semester-name { font-family: var(--font-display); font-weight: 600; font-size: 0.95rem; }
.semester-count { color: var(--ink-muted); font-size: 0.8rem; margin-top: 0.3rem; }

.chapter-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.chapter-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.85rem 1rem;
    background: var(--paper);
    border: 1.5px solid rgba(15, 23, 42, 0.06);
    border-radius: var(--radius);
    text-decoration: none;
    color: var(--ink);
    transition: var(--transition);
}

.chapter-item:hover {
    border-color: var(--gold);
    background: var(--gold-bg);
    transform: translateX(4px);
}

.chapter-name { flex: 1; font-weight: 500; }
.chapter-count { color: var(--ink-muted); font-size: 0.85rem; }
.chapter-action { color: var(--gold); font-size: 0.85rem; font-weight: 500; }

.question-preview-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.question-preview-item {
    padding: 0.7rem 1rem;
    background: var(--ivory-dark);
    border-radius: var(--radius-sm);
    border-left: 3px solid var(--gold);
}

.question-preview-meta {
    display: flex;
    gap: 0.4rem;
    margin-bottom: 0.3rem;
}

.question-preview-content {
    font-size: 0.9rem;
    color: var(--ink-light);
    line-height: 1.5;
}

.section-title {
    font-family: var(--font-display);
    font-size: 1rem;
    font-weight: 600;
    color: var(--ink-light);
    margin-bottom: 0.8rem;
    padding-bottom: 0.4rem;
    border-bottom: 1px dashed rgba(15, 23, 42, 0.1);
}

.custom-fields-section {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 2px solid var(--ivory-dark);
}

.inline-input {
    padding: 0.3rem 0.5rem;
    border: 1px solid rgba(15, 23, 42, 0.1);
    border-radius: var(--radius-sm);
    font-size: 0.85rem;
    width: 100%;
    max-width: 200px;
    font-family: var(--font-body);
}

.inline-select {
    padding: 0.3rem 0.5rem;
    border: 1px solid rgba(15, 23, 42, 0.1);
    border-radius: var(--radius-sm);
    font-size: 0.85rem;
}

.checkbox-label {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    cursor: pointer;
    font-size: 0.9rem;
}

.hint { color: var(--ink-muted); font-size: 0.85rem; margin-bottom: 0.8rem; }

code {
    background: var(--ivory-dark);
    padding: 0.1rem 0.4rem;
    border-radius: 3px;
    font-family: var(--font-mono);
    font-size: 0.85rem;
    color: var(--danger);
}

.achievement-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin-bottom: 1rem;
}

.achievement-item {
    text-align: center;
    padding: 1rem 0.5rem;
    background: var(--gold-bg);
    border-radius: var(--radius-lg);
}

.achievement-icon { font-size: 1.6rem; margin-bottom: 0.3rem; }

.achievement-value {
    font-family: var(--font-display);
    font-size: 1.5rem;
    font-weight: bold;
    color: var(--ink);
}

.achievement-label { color: var(--ink-muted); font-size: 0.8rem; margin-top: 0.2rem; }

.achievement-progress-track {
    height: 6px;
    background: var(--ivory-dark);
    border-radius: 3px;
    margin-top: 0.5rem;
    overflow: hidden;
}

.achievement-progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--gold), var(--gold-light));
    border-radius: 3px;
    transition: width 0.4s ease;
}

.accuracy-up { color: var(--success); }
.accuracy-down { color: var(--danger); }
.accuracy-flat { color: var(--ink-muted); }

.badge-section {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(15, 23, 42, 0.06);
}

.badge-section-title {
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--ink-light);
    margin-bottom: 0.6rem;
}

.badge-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.chapter-badge {
    display: inline-block;
    padding: 0.3rem 0.7rem;
    background: linear-gradient(135deg, var(--success-bg), #dcfce7);
    color: var(--success);
    border-radius: 14px;
    font-size: 0.8rem;
    font-weight: 500;
}

[data-theme="dark"] .chapter-badge {
    background: #052e16;
    color: #4ade80;
}

[data-theme="dark"] .achievement-item {
    background: rgba(212, 168, 83, 0.08);
}

[data-theme="dark"] .feature-item {
    background: rgba(212, 168, 83, 0.08);
}

[data-theme="dark"] .action-card {
    background: rgba(212, 168, 83, 0.08);
}

[data-theme="dark"] .action-card:hover {
    background: var(--paper);
}

[data-theme="dark"] .subject-card,
[data-theme="dark"] .semester-card {
    background: var(--paper);
    border-color: rgba(255, 255, 255, 0.08);
}

[data-theme="dark"] .chapter-item {
    background: var(--paper);
    border-color: rgba(255, 255, 255, 0.08);
}

[data-theme="dark"] .chapter-item:hover {
    background: var(--gold-bg);
}

[data-theme="dark"] .question-preview-item {
    background: var(--ivory-dark);
    border-color: rgba(255, 255, 255, 0.08);
}

[data-theme="dark"] .weak-item {
    background: var(--paper);
    border-color: rgba(255, 255, 255, 0.08);
}

[data-theme="dark"] .result-explanation {
    background: rgba(212, 168, 83, 0.08);
}

[data-theme="dark"] .format-example {
    background: #0c1222;
}

[data-theme="dark"] .hero h1 {
    color: var(--ink);
}

#feedback-widget {
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 1000;
}

#feedback-toggle {
    background: var(--gold);
    color: var(--ink);
    border: none;
    padding: 0.6rem 1.2rem;
    border-radius: 20px;
    cursor: pointer;
    font-size: 0.85rem;
    font-weight: 600;
    font-family: var(--font-body);
    box-shadow: 0 2px 8px rgba(212, 168, 83, 0.3);
    transition: var(--transition);
}

#feedback-toggle:hover {
    background: var(--gold-light);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(212, 168, 83, 0.4);
}

#feedback-form-wrap {
    position: absolute;
    bottom: 50px;
    right: 0;
    width: 300px;
    background: var(--paper);
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: var(--radius-lg);
    padding: 1rem;
    box-shadow: var(--paper-shadow-elevated);
}

#feedback-form textarea {
    width: 100%;
    padding: 0.6rem;
    border: 1.5px solid rgba(15, 23, 42, 0.1);
    border-radius: var(--radius);
    font-size: 0.85rem;
    resize: vertical;
    margin-bottom: 0.5rem;
    box-sizing: border-box;
    font-family: var(--font-body);
    background: var(--paper);
    color: var(--ink);
}

#feedback-form button[type="submit"] {
    width: 100%;
    padding: 0.5rem;
    background: var(--gold);
    color: var(--ink);
    border: none;
    border-radius: var(--radius);
    cursor: pointer;
    font-size: 0.85rem;
    font-weight: 600;
    font-family: var(--font-body);
    transition: var(--transition);
}

#feedback-form button[type="submit"]:hover {
    background: var(--gold-light);
}

#feedback-success {
    text-align: center;
    color: var(--success);
    font-weight: 500;
    margin: 0;
    padding: 0.5rem 0;
}

[data-theme="dark"] #feedback-form-wrap {
    border-color: rgba(255, 255, 255, 0.08);
}

.theme-toggle {
    background: none;
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 50%;
    width: 36px;
    height: 36px;
    cursor: pointer;
    font-size: 1.1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: var(--transition);
}

.theme-toggle:hover {
    background: rgba(255, 255, 255, 0.08);
    transform: rotate(15deg);
}

@media (max-width: 600px) {
    .stats-row { grid-template-columns: repeat(3, 1fr); }
    .stats-row-4 { grid-template-columns: repeat(2, 1fr); }
    .form-row { grid-template-columns: 1fr; }
    .form-row-2col { grid-template-columns: 1fr; }
    .feature-grid { grid-template-columns: 1fr; }
    .quick-actions { grid-template-columns: repeat(2, 1fr); }
    .nav-links { gap: 0.15rem; }
    .nav-link { padding: 0.25rem 0.4rem; font-size: 0.78rem; }
    .bar-label { width: 50px; font-size: 0.8rem; }
    .btn-group { flex-wrap: wrap; }
    .filter-group { margin-bottom: 0.5rem; }
    .flex-between { flex-direction: column; align-items: flex-start; }
    .option-label { padding: 0.8rem; min-height: 44px; }
    .submit-bar { padding: 0.8rem; }
    .data-table { font-size: 0.8rem; }
    .data-table th, .data-table td { padding: 0.5rem 0.3rem; }
    .semester-grid { grid-template-columns: repeat(2, 1fr); }
    .chapter-item { padding: 0.7rem; }
    .achievement-grid { grid-template-columns: 1fr; }
    .auth-card { margin: 1.5rem auto; padding: 1.5rem; }
}
```

- [ ] **Step 2: 修改 base.html — 加载新字体**

在 `app/templates/base.html` 的 `<head>` 中，在 `<link rel="stylesheet" href="/static/style.css">` 之前添加 Google Fonts：

```html
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;600;700&family=Noto+Serif+SC:wght@600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

同时修改 `<meta name="theme-color" content="#4361ee">` 为：
```html
    <meta name="theme-color" content="#0f172a">
```

- [ ] **Step 3: 运行全量测试确认无回归**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/ --tb=short -q`
Expected: 全部 PASS（CSS 和模板变更不影响 Python 测试）

- [ ] **Step 4: Commit**

```bash
git add app/static/style.css app/templates/base.html
git commit -m "design: scholarly refinement design system - CSS overhaul with gold/ink/ivory palette"
```

---

### Task 2: 认证页面视觉升级

**Files:**
- Modify: `app/templates/login.html`
- Modify: `app/templates/register.html`
- Modify: `app/templates/recover.html`
- Modify: `app/templates/recover_submitted.html`

- [ ] **Step 1: 升级登录页面**

替换 `app/templates/login.html`：

```html
{% extends "base.html" %}
{% block title %}登录 - 付刷{% endblock %}
{% block content %}
<div class="auth-card">
    <h1>欢迎回来</h1>
    {% if error %}
    <div class="alert alert-error">{{ error }}</div>
    {% endif %}
    <form action="/login" method="post">
        <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
        <div class="form-group">
            <label for="username">用户名</label>
            <input type="text" id="username" name="username" required placeholder="请输入用户名" autofocus>
        </div>
        <div class="form-group">
            <label for="password">密码</label>
            <input type="password" id="password" name="password" required placeholder="请输入密码">
        </div>
        <button type="submit" class="btn btn-primary btn-block btn-lg">登录</button>
    </form>
    <p style="text-align:center;margin-top:0.6rem;"><a href="/recover" style="color:var(--ink-muted);font-size:0.88rem;">忘记密码？找回账号</a></p>
    <p class="auth-switch">还没有账号？<a href="/register">立即注册</a></p>
</div>
{% endblock %}
```

- [ ] **Step 2: 升级注册页面**

替换 `app/templates/register.html`：

```html
{% extends "base.html" %}
{% block title %}注册 - 付刷{% endblock %}
{% block content %}
<div class="auth-card">
    <h1>创建账号</h1>
    {% if error %}
    <div class="alert alert-error">{{ error }}</div>
    {% endif %}
    <form action="/register" method="post">
        <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
        <div class="form-group">
            <label for="username">用户名</label>
            <input type="text" id="username" name="username" required placeholder="请输入用户名">
        </div>
        <div class="form-group">
            <label for="display_name">昵称</label>
            <input type="text" id="display_name" name="display_name" placeholder="显示名称（可选）">
        </div>
        <div class="form-group">
            <label for="password">密码</label>
            <input type="password" id="password" name="password" required placeholder="至少6位，非纯数字">
        </div>
        <div class="form-group">
            <label>我是</label>
            <div class="role-select" style="display:flex;gap:0.8rem;flex-wrap:wrap;">
                <label style="cursor:pointer;flex:1;text-align:center;padding:0.7rem;border:2px solid var(--ivory-dark);border-radius:var(--radius);transition:var(--transition);font-weight:500;" class="role-option" onclick="toggleFields()">
                    <input type="radio" name="role" value="student" checked style="margin-right:0.3rem;"> 🎓 学生
                </label>
                <label style="cursor:pointer;flex:1;text-align:center;padding:0.7rem;border:2px solid var(--ivory-dark);border-radius:var(--radius);transition:var(--transition);font-weight:500;" class="role-option" onclick="toggleFields()">
                    <input type="radio" name="role" value="teacher" style="margin-right:0.3rem;"> 👨‍🏫 教师
                </label>
                <label style="cursor:pointer;flex:1;text-align:center;padding:0.7rem;border:2px solid var(--ivory-dark);border-radius:var(--radius);transition:var(--transition);font-weight:500;" class="role-option" onclick="toggleFields()">
                    <input type="radio" name="role" value="admin" style="margin-right:0.3rem;"> 🛡️ 管理员
                </label>
            </div>
        </div>
        <div id="studentModeGroup">
            <div class="form-group">
                <label>注册方式</label>
                <div style="display:flex;flex-direction:column;gap:0.6rem;margin-top:0.4rem;">
                    <label style="cursor:pointer;padding:0.7rem;border:2px solid var(--ivory-dark);border-radius:var(--radius);transition:var(--transition);" class="join-mode-option" data-mode="formal">
                        <input type="radio" name="join_mode" value="formal" onchange="toggleJoinMode()" style="margin-right:0.4rem;">
                        <strong>✅ 正式加入班级</strong>
                        <div style="color:var(--ink-muted);font-size:0.82rem;margin-top:0.2rem;">选择班级后立即加入，可使用全部功能</div>
                    </label>
                    <label style="cursor:pointer;padding:0.7rem;border:2px solid var(--ivory-dark);border-radius:var(--radius);transition:var(--transition);" class="join-mode-option" data-mode="apply">
                        <input type="radio" name="join_mode" value="apply" onchange="toggleJoinMode()" style="margin-right:0.4rem;">
                        <strong>📝 申请加入班级</strong>
                        <div style="color:var(--ink-muted);font-size:0.82rem;margin-top:0.2rem;">提交申请，等待教师审核通过后正式加入</div>
                    </label>
                    <label style="cursor:pointer;padding:0.7rem;border:2px solid var(--ivory-dark);border-radius:var(--radius);transition:var(--transition);" class="join-mode-option" data-mode="guest">
                        <input type="radio" name="join_mode" value="guest" onchange="toggleJoinMode()" style="margin-right:0.4rem;">
                        <strong>👀 临时游客</strong>
                        <div style="color:var(--ink-muted);font-size:0.82rem;margin-top:0.2rem;">无需选择班级，仅可体验1小时</div>
                    </label>
                </div>
            </div>
            <div class="form-group" id="classSelectGroup" style="display:none;">
                <label for="class_id">选择班级</label>
                <select name="class_id" id="class_id">
                    <option value="">请选择班级</option>
                    {% for c in classes %}
                    <option value="{{ c.id }}" {{ 'selected' if c.id|string == preselected_class else '' }}>{{ c.name }}</option>
                    {% endfor %}
                </select>
            </div>
        </div>
        <div class="form-group" id="inviteCodeGroup" style="display:none;">
            <label for="invite_code">邀请码 *</label>
            <input type="text" id="invite_code" name="invite_code" placeholder="请输入邀请码">
            <small id="inviteCodeHint" style="color:var(--ink-muted);font-size:0.82rem;">教师注册需要邀请码，请联系管理员获取</small>
        </div>
        <button type="submit" class="btn btn-primary btn-block btn-lg">注册</button>
    </form>
    <p class="auth-switch">已有账号？<a href="/login">去登录</a></p>
</div>
<script>
function toggleFields() {
    var role = document.querySelector('input[name="role"]:checked').value;
    var inviteGroup = document.getElementById('inviteCodeGroup');
    var studentGroup = document.getElementById('studentModeGroup');
    var hint = document.getElementById('inviteCodeHint');
    var roleOptions = document.querySelectorAll('.role-option');
    roleOptions.forEach(function(opt) {
        opt.style.borderColor = 'var(--ivory-dark)';
        opt.style.background = '';
    });
    var selected = document.querySelector('.role-option input:checked');
    if (selected && selected.closest('.role-option')) {
        selected.closest('.role-option').style.borderColor = 'var(--gold)';
        selected.closest('.role-option').style.background = 'var(--gold-bg)';
    }
    if (role === 'teacher') {
        inviteGroup.style.display = 'block';
        hint.textContent = '教师注册需要邀请码，请联系管理员获取';
    } else if (role === 'admin') {
        inviteGroup.style.display = 'block';
        hint.textContent = '管理员注册需要管理员邀请码';
    } else {
        inviteGroup.style.display = 'none';
    }
    studentGroup.style.display = role === 'student' ? 'block' : 'none';
}
function toggleJoinMode() {
    var mode = document.querySelector('input[name="join_mode"]:checked');
    var classGroup = document.getElementById('classSelectGroup');
    var options = document.querySelectorAll('.join-mode-option');
    options.forEach(function(opt) {
        opt.style.borderColor = 'var(--ivory-dark)';
        opt.style.background = '';
    });
    if (mode) {
        var selected = document.querySelector('.join-mode-option[data-mode="' + mode.value + '"]');
        if (selected) {
            selected.style.borderColor = 'var(--gold)';
            selected.style.background = 'var(--gold-bg)';
        }
        if (mode.value === 'formal' || mode.value === 'apply') {
            classGroup.style.display = 'block';
        } else {
            classGroup.style.display = 'none';
        }
    } else {
        classGroup.style.display = 'none';
    }
}
document.addEventListener('DOMContentLoaded', function() {
    toggleFields();
    toggleJoinMode();
});
</script>
{% endblock %}
```

- [ ] **Step 3: 升级找回页面**

替换 `app/templates/recover.html`：

```html
{% extends "base.html" %}
{% block title %}找回账号 - 付刷{% endblock %}
{% block content %}
<div class="auth-card">
    <h1>找回账号</h1>
    {% if error %}
    <div class="alert alert-error">{{ error }}</div>
    {% endif %}
    <p style="color:var(--ink-muted);margin-bottom:1.2rem;font-size:0.9rem;">请填写以下信息，提交后由教师或管理员审核并重置密码。</p>
    <form action="/recover" method="post">
        <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
        <div class="form-group">
            <label for="username">用户名 *</label>
            <input type="text" id="username" name="username" required placeholder="请输入注册时的用户名">
        </div>
        <div class="form-group">
            <label for="class_id">所在班级</label>
            <select name="class_id" id="class_id">
                <option value="">请选择（可选）</option>
                {% for c in classes %}
                <option value="{{ c.id }}">{{ c.name }}</option>
                {% endfor %}
            </select>
        </div>
        <div class="form-group">
            <label for="display_name">姓名/昵称</label>
            <input type="text" id="display_name" name="display_name" placeholder="帮助老师确认身份">
        </div>
        <button type="submit" class="btn btn-primary btn-block btn-lg">提交找回申请</button>
    </form>
    <p class="auth-switch"><a href="/login">返回登录</a></p>
</div>
{% endblock %}
```

- [ ] **Step 4: 升级找回成功页面**

替换 `app/templates/recover_submitted.html`：

```html
{% extends "base.html" %}
{% block title %}找回申请已提交 - 付刷{% endblock %}
{% block content %}
<div class="auth-card" style="text-align:center;">
    <div style="font-size:3rem;margin-bottom:1rem;">✅</div>
    <h1>申请已提交</h1>
    <p style="color:var(--ink-muted);margin-bottom:1.5rem;">教师或管理员审核通过后，您的密码将被重置为默认密码，届时请登录后及时修改。</p>
    <a href="/login" class="btn btn-primary btn-lg">返回登录</a>
</div>
{% endblock %}
```

- [ ] **Step 5: 运行全量测试**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/ --tb=short -q`
Expected: 全部 PASS

- [ ] **Step 6: Commit**

```bash
git add app/templates/login.html app/templates/register.html app/templates/recover.html app/templates/recover_submitted.html
git commit -m "design: auth pages visual upgrade - scholarly refinement style"
```

---

### Task 3: 管理后台页面视觉升级

**Files:**
- Modify: `app/templates/admin/index.html`
- Modify: `app/templates/admin/users.html`
- Modify: `app/templates/admin/classes.html`
- Modify: `app/templates/admin/invite.html`
- Modify: `app/templates/admin/recovery_requests.html`

- [ ] **Step 1: 升级管理后台首页**

替换 `app/templates/admin/index.html`：

```html
{% extends "base.html" %}
{% block title %}管理后台 - 付刷{% endblock %}
{% block content %}
<div style="display:flex;align-items:center;gap:0.8rem;margin-bottom:1.5rem;">
    <h1 style="margin-bottom:0;">🛡️ 管理后台</h1>
</div>

<div class="stats-row">
    <div class="stat-card">
        <div class="stat-number">{{ user_count }}</div>
        <div class="stat-label">用户数</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{{ class_count }}</div>
        <div class="stat-label">班级数</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{{ question_count }}</div>
        <div class="stat-label">题目数</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{{ teacher_count }}</div>
        <div class="stat-label">教师数</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{{ guest_count }}</div>
        <div class="stat-label">游客数</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{{ admin_count }}</div>
        <div class="stat-label">管理员数</div>
    </div>
</div>

<div class="card">
    <h2>用户与权限</h2>
    <div style="display:flex;gap:0.6rem;flex-wrap:wrap;">
        <a href="/admin/users" class="btn btn-primary">用户管理</a>
        <a href="/admin/invite" class="btn btn-outline">邀请码管理</a>
        <a href="/admin/recovery-requests" class="btn btn-outline">找回申请</a>
    </div>
</div>

<div class="card">
    <h2>系统维护</h2>
    <div style="display:flex;gap:0.6rem;flex-wrap:wrap;">
        <a href="/admin/classes" class="btn btn-outline">班级管理</a>
        <form action="/admin/cleanup-guests" method="POST" style="display:inline;">
            <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
            <button type="submit" class="btn btn-outline" onclick="return confirm('确定清理所有过期游客？')">清理过期游客</button>
        </form>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 2: 升级邀请码管理页面**

替换 `app/templates/admin/invite.html`：

```html
{% extends "base.html" %}
{% block title %}邀请码管理 - 付刷{% endblock %}
{% block content %}
<h1>邀请码管理</h1>

<div class="card">
    <form action="/admin/invite/update" method="POST">
        <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
        <div class="form-group">
            <label>教师邀请码</label>
            <input type="text" name="teacher_codes" value="{{ teacher_codes }}" placeholder="多个邀请码用逗号分隔">
            <small style="color:var(--ink-muted);font-size:0.82rem;">教师注册时需要输入此邀请码，多个码用英文逗号分隔</small>
        </div>
        <div class="form-group">
            <label>管理员邀请码</label>
            <input type="text" name="admin_codes" value="{{ admin_codes }}" placeholder="多个邀请码用逗号分隔">
            <small style="color:var(--ink-muted);font-size:0.82rem;">管理员注册时需要输入此邀请码，请谨慎分发</small>
        </div>
        <button type="submit" class="btn btn-primary">保存</button>
    </form>
</div>

<a href="/admin" class="btn btn-outline" style="margin-top:0.5rem;">返回管理首页</a>
{% endblock %}
```

- [ ] **Step 3: 升级找回申请页面**

替换 `app/templates/admin/recovery_requests.html`：

```html
{% extends "base.html" %}
{% block title %}找回申请管理 - 付刷{% endblock %}
{% block content %}
<h1>账号找回申请</h1>

{% if pending %}
<div class="card" style="border-left:4px solid var(--gold);">
    <h2>待处理 ({{ pending|length }})</h2>
    <table class="data-table">
        <thead><tr><th>用户名</th><th>班级</th><th>姓名</th><th>申请时间</th><th>操作</th></tr></thead>
        <tbody>
        {% for r in pending %}
        <tr>
            <td><strong>{{ r.username }}</strong></td>
            <td>{{ r.class_id or '—' }}</td>
            <td>{{ r.display_name or '—' }}</td>
            <td>{{ r.created_at.strftime('%m-%d %H:%M') if r.created_at else '' }}</td>
            <td>
                <form action="/admin/recovery-requests/{{ r.id }}/approve" method="POST" style="display:inline;">
                    <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
                    <button type="submit" class="btn btn-primary btn-sm" onclick="return confirm('确定通过？密码将重置为 abc123')">通过</button>
                </form>
                <form action="/admin/recovery-requests/{{ r.id }}/reject" method="POST" style="display:inline;">
                    <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">
                    <button type="submit" class="btn btn-outline btn-sm" onclick="return confirm('确定拒绝？')">拒绝</button>
                </form>
            </td>
        </tr>
        {% endfor %}
        </tbody>
    </table>
</div>
{% else %}
<div class="card">
    <p style="color:var(--ink-muted);text-align:center;padding:1.5rem 0;">暂无待处理的找回申请。</p>
</div>
{% endif %}

{% if processed %}
<div class="card">
    <h2>已处理</h2>
    <table class="data-table">
        <thead><tr><th>用户名</th><th>姓名</th><th>状态</th><th>处理时间</th></tr></thead>
        <tbody>
        {% for r in processed %}
        <tr>
            <td>{{ r.username }}</td>
            <td>{{ r.display_name or '—' }}</td>
            <td>{% if r.status == 'approved' %}<span class="badge badge-correct">已通过</span>{% else %}<span class="badge badge-wrong">已拒绝</span>{% endif %}</td>
            <td>{{ r.reviewed_at.strftime('%m-%d %H:%M') if r.reviewed_at else '' }}</td>
        </tr>
        {% endfor %}
        </tbody>
    </table>
</div>
{% endif %}

<a href="/admin" class="btn btn-outline" style="margin-top:0.5rem;">返回管理首页</a>
{% endblock %}
```

- [ ] **Step 4: 升级班级管理页面**

替换 `app/templates/admin/classes.html`：

```html
{% extends "base.html" %}
{% block title %}班级管理 - 付刷{% endblock %}
{% block content %}
<h1>班级管理</h1>

{% if class_data %}
<div class="card">
    <table class="data-table">
        <thead><tr><th>班级名称</th><th>创建者</th><th>学生数</th><th>创建时间</th></tr></thead>
        <tbody>
        {% for c in class_data %}
        <tr>
            <td><strong>{{ c.name }}</strong></td>
            <td>{{ c.created_by }}</td>
            <td>{{ c.member_count }}</td>
            <td>{{ c.created_at.strftime('%Y-%m-%d %H:%M') if c.created_at else '' }}</td>
        </tr>
        {% endfor %}
        </tbody>
    </table>
</div>
{% else %}
<div class="card">
    <p style="color:var(--ink-muted);text-align:center;padding:1.5rem 0;">暂无班级。</p>
</div>
{% endif %}

<a href="/admin" class="btn btn-outline" style="margin-top:0.5rem;">返回管理首页</a>
{% endblock %}
```

- [ ] **Step 5: 运行全量测试**

Run: `C:\Users\Windows 10\python-sdk\python3.13.2\python.exe -m pytest tests/ --tb=short -q`
Expected: 全部 PASS

- [ ] **Step 6: Commit**

```bash
git add app/templates/admin/
git commit -m "design: admin pages visual upgrade - scholarly refinement style"
```

---

## 自查清单

### 1. 需求覆盖

| 需求 | 对应 Task |
|------|-----------|
| CSS 设计系统重构 | Task 1 |
| 字体升级（衬线+无衬线+等宽） | Task 1 |
| 配色升级（墨+金+象牙） | Task 1 |
| 深色模式适配 | Task 1 |
| 登录页视觉升级 | Task 2 |
| 注册页视觉升级 | Task 2 |
| 找回页视觉升级 | Task 2 |
| 管理后台首页升级 | Task 3 |
| 邀请码管理页升级 | Task 3 |
| 找回申请页升级 | Task 3 |
| 班级管理页升级 | Task 3 |

### 2. 占位符扫描

无 TBD/TODO 等占位符。

### 3. 类型一致性

- CSS 变量名统一：`--ink`, `--gold`, `--ivory`, `--paper`, `--success`, `--danger`, `--warning`, `--info`
- 字体变量统一：`--font-display`, `--font-body`, `--font-mono`
- 圆角变量统一：`--radius-sm`, `--radius`, `--radius-lg`, `--radius-xl`
- 所有模板中引用的 CSS 类名与 style.css 中的定义一致
