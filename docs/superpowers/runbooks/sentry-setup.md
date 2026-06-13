# Sentry 接入 — 部署期操作

代码层 Plan 1.4 已就绪（`app/core/observability.py`）。DSN 为空时 noop，部署时按本文档操作启用。

## 1. 申请 Sentry 项目

1. 访问 https://sentry.io/signup/ 注册账号
2. Organizations → Projects → Create Project
3. Platform 选 **Python → FastAPI**
4. Project name: `fushua-prod`（或 `fushua-staging`）
5. 创建后，Settings → Client Keys (DSN) 复制 DSN 字符串，形如 `https://abc123@o0.ingest.sentry.io/0`

## 2. 注入环境变量

添加环境变量：
- `SENTRY_DSN` = 上步复制的 DSN
- `SENTRY_TRACES_SAMPLE_RATE` = `0.1`（10% 性能追踪采样）
- `ENVIRONMENT` = `production`

## 3. 验证上报

人为触发异常后，登录 Sentry → Issues 列表确认收到。

也可用临时测试端点：
```python
# app/api/v1/ 临时增加（验证后即删）
@router.get("/__sentry_test")
def sentry_test():
    raise RuntimeError("Sentry test trigger")
```

## 4. 故障排查

| 现象 | 排查 |
|------|------|
| 收不到事件 | 检查 SENTRY_DSN、网络出站 |
| environment 标错 | 检查 ENVIRONMENT 环境变量 |
| 收到 PII | `send_default_pii=False` 已设 |

## 5. 小程序错误上报

小程序在 `app.js` 的 `App.onError` 调用：
```javascript
App({
  onError(err) {
    wx.request({
      url: `${this.globalData.baseUrl}/api/v1/client-error`,
      method: 'POST',
      data: { message: String(err), page: getCurrentPages().slice(-1)[0]?.route || '', platform: 'wechat-miniprogram', ts: Date.now() },
    });
  },
});
```
后端会写 structlog 并转发 Sentry。
