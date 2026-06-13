# 阿里云部署实测方案

更新时间：2026-05-25

## 1. 环境范围

- 服务器：阿里云 ECS，Ubuntu 22.04，2 vCPU，2 GiB 内存。
- 公网地址：`http://8.137.198.33`
- 后端入口：`http://8.137.198.33/api/v1`
- Web 入口：`http://8.137.198.33`
- 小程序本地开发配置：`miniprogram/config.js` 的生产地址为 `http://8.137.198.33`。

当前使用公网 IP + HTTP 完成联调。微信小程序正式发布前，需要完成域名备案、HTTPS 证书配置，并在微信公众平台配置 request 合法域名。

## 2. 测试账号

生产环境已创建一组三角色测试账号，密码保存在服务器 `/root/fushua-deploy-credentials-20260525.txt`。

- 管理员：`codex_admin`
- 教师：`codex_teacher`
- 学生：`codex_student`

验收完成后，应修改密码或删除测试账号。

## 3. Web 端实测清单

### 3.1 公开页面

1. 打开 `http://8.137.198.33/`，确认首页可访问。
2. 打开 `/login`，确认登录表单可访问。
3. 打开 `/register`，确认注册表单可访问。
4. 打开 `/help`，确认帮助页可访问。

通过标准：页面状态码为 200，页面无服务端错误。

### 3.2 管理员

1. 使用 `codex_admin` 登录。
2. 进入 `/admin`，确认统计卡片、用户管理、班级管理、邀请码、数据恢复、备份、审计、批量清理、公告、导出等入口可见。
3. 进入 `/admin/users`，确认用户列表可访问。
4. 进入 `/admin/classes`，确认班级列表可访问。
5. 进入 `/admin/backup`，触发一次备份，确认生成成功记录。
6. 对最新备份执行验证，确认备份文件可读。

通过标准：管理员页面均可访问；备份触发返回成功；服务器 `backups/` 下出现 `.sql.gz` 文件。

### 3.3 教师

1. 使用 `codex_teacher` 登录。
2. 创建班级，记录班级码。
3. 创建一道题目，确认正确答案能保存。
4. 创建作业并选择题目。
5. 查看班级成员和作业列表。
6. 导出或查看统计页面，确认教师数据可访问。

通过标准：班级、题目、作业均可创建；学生加入后教师端可见。

### 3.4 学生

1. 使用 `codex_student` 登录。
2. 使用教师班级码加入班级。
3. 进入刷题页面，加载随机题目。
4. 提交练习记录。
5. 查看今日统计、错题、个人统计。
6. 打开作业详情，提交作业答案。
7. 查看作业提交状态。

通过标准：学生可加入班级、刷题、提交练习记录、查看统计、完成作业。

## 4. 小程序端实测清单

### 4.1 开发者工具准备

1. 微信开发者工具打开 `miniprogram` 目录。
2. 确认 `project.config.json` 使用当前小程序 AppID。
3. 在本地用 IP + HTTP 调试时，开发者工具需要开启“不校验合法域名、web-view、TLS 版本以及 HTTPS 证书”。
4. 确认 `miniprogram/config.js` 生产环境地址为 `http://8.137.198.33`。

### 4.2 学生路径

1. 打开小程序，完成登录或身份绑定。
2. 加入班级。
3. 进入刷题页面，加载题目。
4. 提交练习记录。
5. 查看今日统计、错题本、个人统计。
6. 打开作业详情，提交作业。
7. 再次进入作业，确认已完成状态。

通过标准：所有接口请求落到 `http://8.137.198.33/api/v1`；无 404；关键接口返回 `correct_answer`、统计和提交状态。

### 4.3 教师路径

1. 教师身份进入班级页面。
2. 查看班级成员。
3. 查看题目和作业。
4. 删除测试班级成员后，确认成员列表更新。

通过标准：教师可管理班级与成员，接口无鉴权或字段兼容错误。

## 5. 本次自动化实测证据

- 本地全量测试：`python -m pytest tests/ -q --tb=short --disable-warnings --maxfail=1`，结果 `538 passed`。
- 小程序兼容测试：`tests/test_miniprogram_compat.py`，覆盖练习记录、统计、错题、作业详情、作业提交、班级成员删除。
- 小程序请求地址测试：`tests/miniprogram_request_url.test.js`，覆盖 `/api/v1` 前缀兼容。
- 部署脚本测试：`tests/test_deployment_scripts.py`，覆盖 systemd PATH 和 PostgreSQL 备份 URL 解析。
- 生产健康检查：`GET http://8.137.198.33/health` 返回 200。
- 生产 Web 页面冒烟：登录、管理员页、用户页、班级页、备份页、题库浏览、帮助页均返回 200。
- 生产 API 冒烟：管理员、教师、学生登录成功；教师创建班级/题目/作业成功；学生加入班级、刷题、提交作业成功。
- 生产备份触发：`POST /admin/backup/trigger` 返回 200，并生成 `fushua_20260525_233845.sql.gz`。
- 生产备份验证：`POST /admin/backup/validate/2` 返回 `status=valid`。

## 6. 回滚方案

部署前已在服务器保留快照：

- 应用备份：`/root/fushua-backups/20260525-230235`
- 上一版应用目录：`/var/www/fushua.prev-20260525-231553`

需要回滚时：

```bash
systemctl stop fushua
mv /var/www/fushua /var/www/fushua.failed-$(date +%Y%m%d-%H%M%S)
mv /var/www/fushua.prev-20260525-231553 /var/www/fushua
systemctl start fushua
systemctl status fushua
```

如果数据库也需要回滚，先从 `/root/fushua-backups/20260525-230235/database.sql.gz` 恢复，并在恢复前再次备份当前数据库。

## 7. 正式发布前待办

1. 绑定正式域名并完成备案。
2. 配置 HTTPS。
3. 在微信公众平台添加 `https://正式域名` 到 request 合法域名。
4. 将 `miniprogram/config.js` 的生产地址改为 HTTPS 域名。
5. 删除或改密测试账号。
6. 配置每日自动备份和定期恢复演练。
