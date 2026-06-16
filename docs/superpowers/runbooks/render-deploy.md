# Render 生产部署指南

## 1. 数据库切换 SQLite → PostgreSQL

### 1.1 Render 上创建 PostgreSQL
1. Render Dashboard → New → PostgreSQL
2. Name: `fushua-db`
3. Plan: Free (1 GB)
4. 创建后复制 Internal Database URL

### 1.2 环境变量配置
在 Render Web Service → Environment 添加：

```
DATABASE_URL=postgresql://<user>:<pass>@<host>:5432/<db>
ENVIRONMENT=production
SENTRY_DSN=<sentry DSN>
SENTRY_TRACES_SAMPLE_RATE=0.05
SECRET_KEY=<random 64-char string>
HTTPS_ONLY=true
WECHAT_APPID=<微信小程序 AppID>
WECHAT_SECRET=<微信小程序 Secret>
```

### 1.3 启动命令
```bash
alembic upgrade head
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT
```

### 1.4 验证
```bash
curl https://fushua.onrender.com/health
# 预期: {"status":"ok","db_ok":true,...}
```

## 2. Ping 保活
Render free tier 15 分钟无流量会休眠。用 cron-job.org 或 uptimerobot 每 10 分钟 ping `/health`。
