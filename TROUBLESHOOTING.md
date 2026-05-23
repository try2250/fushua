# 问题排查和解决方案

## 问题1：Web端403错误

### 可能原因：
1. Render还在部署中，新代码未生效
2. 浏览器缓存了旧的session
3. 访问的URL不正确

### 解决步骤：

**步骤1：检查Render部署状态**
1. 访问 Render Dashboard
2. 查看最新部署是否完成
3. 查看部署日志是否有错误

**步骤2：确认访问正确的URL**
正确的URL应该是：
```
https://fushua.onrender.com/admin/announcements
```

**步骤3：清除浏览器缓存**
```
Chrome: 
1. 按 F12 打开开发者工具
2. 右键点击刷新按钮
3. 选择"清空缓存并硬性重新加载"

或者使用无痕模式：
Ctrl + Shift + N
```

**步骤4：检查登录状态**
```
1. 访问 https://fushua.onrender.com/logout
2. 重新登录
3. 再次访问公告页面
```

**步骤5：查看浏览器控制台错误**
```
1. 按 F12 打开开发者工具
2. 切换到 Console 标签
3. 访问公告页面
4. 查看是否有错误信息
```

---

## 问题2：小程序模拟器启动失败

### 错误信息：
```
TypeError: Failed to fetch
模拟器启动失败
请查看构造日志或调试器日志获取更多信息
```

### 原因：
小程序尝试请求API，但域名校验失败

### 解决方案：

**方案1：关闭域名校验（推荐用于开发）**

1. 在微信开发者工具中：
   - 点击右上角"详情"
   - 切换到"本地设置"标签
   - 勾选以下选项：
     ✅ 不校验合法域名、web-view（业务域名）、TLS 版本以及 HTTPS 证书
     ✅ 不校验 Secure 域名
   
2. 点击工具栏的"编译"按钮重新编译

**方案2：配置合法域名（用于真机测试和发布）**

1. 登录微信公众平台：https://mp.weixin.qq.com/
2. 开发 → 开发管理 → 开发设置 → 服务器域名
3. 点击"修改"
4. 在"request合法域名"中添加：
   ```
   https://fushua.onrender.com
   ```
5. 保存并等待5分钟生效

**方案3：检查网络连接**

1. 确认电脑可以访问：https://fushua.onrender.com
2. 检查是否有代理或防火墙阻止
3. 尝试关闭VPN

**方案4：重启开发者工具**

1. 完全关闭微信开发者工具
2. 重新打开
3. 重新导入项目

---

## 快速验证步骤

### 验证Web端：

```bash
# 1. 检查API是否正常
curl https://fushua.onrender.com/docs

# 2. 检查管理后台是否可访问
# 在浏览器访问：
https://fushua.onrender.com/admin

# 3. 检查公告API（需要登录）
# 在浏览器访问：
https://fushua.onrender.com/admin/announcements
```

### 验证小程序：

1. **检查配置**
   - 打开 `miniprogram/config.js`
   - 确认 baseUrl: `https://fushua.onrender.com/api/v1`
   - 确认 ENV: `production`

2. **开发者工具设置**
   - 详情 → 本地设置 → 不校验合法域名 ✅
   - 详情 → 本地设置 → 不校验TLS版本 ✅

3. **重新编译**
   - 点击"编译"按钮
   - 查看控制台是否有错误

---

## 如果问题仍然存在

请提供以下信息：

1. **Web端：**
   - 浏览器控制台的完整错误信息
   - 访问的完整URL
   - Render部署状态（是否显示"Live"）

2. **小程序端：**
   - 开发者工具控制台的完整错误
   - 是否已勾选"不校验合法域名"
   - 网络请求是否成功（Network标签）

---

## 临时测试方案

如果Render部署有问题，可以先在本地测试：

**启动本地后端：**
```bash
cd /c/Users/Windows\ 10/Desktop/trae/fushua
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**修改小程序配置：**
```javascript
// miniprogram/config.js
const ENV = 'development';  // 改为development
```

**访问本地管理后台：**
```
http://localhost:8000/admin
```

这样可以先验证功能是否正常，然后再解决部署问题。
