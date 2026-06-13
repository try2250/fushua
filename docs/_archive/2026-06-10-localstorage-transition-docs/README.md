# 2026-06-10 归档说明：localStorage 过渡期文档

这些文件记录了课堂伴侣从独立网页工具接入到 Fushua 后台的早期过渡方案。它们没有删除，因为里面仍有历史背景、接口片段和阶段记录；但它们不再作为下一步开发依据。

## 为什么归档

当前产品方向已经从“localStorage + API 双模式，可手动切换”调整为：

- 课堂伴侣业务数据必须以云端数据库为唯一事实来源。
- Web 端不再提供“启用 API 模式”开关。
- 浏览器本地存储只能保存非业务偏好，例如主题、折叠状态、最近打开的 tab。
- 课堂抽取、积分、题目快照、课堂会话、统计数据必须通过后端 API 写入数据库。
- API 失败时应显示明确错误和重试入口，不应静默降级到 localStorage。

旧文档中关于“默认 localStorage”“双模式支持”“离线降级”“迁移历史数据按钮”“可交付生产使用”的描述，会误导下一阶段开发。

## 已归档文件

- `classroom-frontend-migration-guide.md`
- `final-implementation-report.md`
- `project-completion-summary.md`
- `phase-b-classroom-web-integration.md`
- `phase-c-classroom-service.md`
- `phase-d-three-module-integration.md`
- `three-module-platform-handoff-plan.md`

## 新的开发入口

请以后优先阅读：

- `docs/superpowers/specs/2026-06-10-integrated-teaching-tools-cloud-design.md`
- `docs/superpowers/plans/2026-06-10-integrated-teaching-tools-cloud-plan.md`

