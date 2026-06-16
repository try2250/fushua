# Sentry Alert Rule 配置

## 1. 登录 Sentry

访问 https://sentry.io，进入 fushua-prod 项目。

## 2. 创建 Alert Rule

Alerts → Create Alert Rule → 选择 **Issues** 类型：

| 配置项 | 值 |
|--------|-----|
| Name | `High Error Rate (>5%)` |
| When | `event.type:error` |
| Threshold | `error_rate > 5% over 5 minutes` |
| Action | Send email notification |
| Recipient | 你的邮箱 |

## 3. 验证

临时触发一个 error（生产环境小心使用）：
```bash
curl https://fushua.onrender.com/api/v1/__trigger_500
# 预期 500 → Sentry 收事件 → Alert 触发 → 收邮件
```

## 4. 日常监控

Sentry Dashboard → Issues 列表 → 检查是否有新 issue。
每周回顾一次，关闭已修复的 issue。
