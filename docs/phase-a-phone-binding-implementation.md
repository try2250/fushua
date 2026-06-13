# 阶段 A 实现文档：手机号绑定开关

实施日期：2026-06-10  
状态：✅ 已完成并测试通过

## 实施目标

根据 `docs/three-module-platform-handoff-plan.md` 阶段 A 要求，实现手机号绑定的短信验证码开关，允许开发期免验证码绑定。

## 已完成的工作

### 1. 后端配置（`app/core/config.py`）

添加配置项：

```python
PHONE_BINDING_REQUIRE_SMS: bool = os.getenv("PHONE_BINDING_REQUIRE_SMS", "false").lower() == "true"
```

- 默认值：`false`（开发期免验证码）
- 通过环境变量 `PHONE_BINDING_REQUIRE_SMS=true` 可切换到生产模式

### 2. 绑定接口逻辑（`app/api/v1/auth.py`）

修改 `/api/v1/auth/wechat/bind` 接口：

- 导入 `settings` 配置
- 根据 `settings.PHONE_BINDING_REQUIRE_SMS` 决定是否校验验证码
- `is_phone_verified` 字段根据配置正确设置：
  - `PHONE_BINDING_REQUIRE_SMS=false` → `is_phone_verified=false`
  - `PHONE_BINDING_REQUIRE_SMS=true` → `is_phone_verified=true`
- 保留所有原有验证逻辑（手机号重复检查、openid_token 验证等）

修改 `/api/v1/auth/sms/send` 接口：

- 开发期返回提示："开发期验证码已跳过，可直接绑定"
- 保留验证码生成逻辑（为后续短信服务接入做准备）

### 3. Schema 调整（`app/schemas/auth.py`）

修改 `WechatBindRequest`：

```python
code: str = Field(default="", description="验证码（开发期可为空）")
```

- 允许 `code` 字段为空字符串
- 移除原有的 `min_length=6` 限制

### 4. 小程序配置（`miniprogram/config.js`）

添加配置项：

```javascript
phoneBindingRequireSms: false
```

- 与后端配置保持一致
- 控制前端验证码输入框显示和校验逻辑

### 5. 小程序绑定页面（`miniprogram/pages/bind/`）

**bind.js 修改：**

- 在 `data` 中读取 `config.APP_CONFIG.phoneBindingRequireSms`
- `nextStep()` 方法中，开发期跳过验证码校验

**bind.wxml 修改：**

- 添加开发期提示框（黄色警告样式）
- 根据 `phoneBindingRequireSms` 条件渲染验证码输入框
- 开发期不显示验证码输入和发送按钮

**bind.wxss 修改：**

- 添加 `.dev-notice` 和 `.notice-text` 样式
- 黄色左边框警告样式

### 6. 测试文件（`tests/test_wechat_binding.py`）

创建完整的测试套件，包含 5 个测试用例：

1. ✅ `test_bind_without_sms_when_disabled` - 免验证码绑定成功
2. ✅ `test_bind_with_wrong_phone_format` - 错误手机号格式（预留）
3. ✅ `test_bind_duplicate_phone` - 重复手机号拦截
4. ✅ `test_bind_with_sms_enabled` - 正确验证码绑定
5. ✅ `test_bind_with_sms_enabled_wrong_code` - 错误验证码拦截

所有测试通过。

## 验收结果

✅ 所有文档要求的验收标准已达成：

- [x] 新微信用户登录后进入绑定页
- [x] 输入合法手机号即可继续选择身份（开发期）
- [x] 学生/教师可以完成绑定
- [x] 数据库中 `phone` 有值，`is_phone_verified=false`（开发期）
- [x] 配置切回 `PHONE_BINDING_REQUIRE_SMS=true` 后，旧验证码逻辑仍可用
- [x] 所有测试通过

## 文件清单

### 修改的文件

```
app/core/config.py                    # 添加配置项
app/api/v1/auth.py                    # 修改绑定和发送短信接口
app/schemas/auth.py                   # 调整 code 字段验证
miniprogram/config.js                 # 添加前端配置
miniprogram/pages/bind/bind.js        # 跳过验证码校验逻辑
miniprogram/pages/bind/bind.wxml      # 条件渲染验证码输入
miniprogram/pages/bind/bind.wxss      # 开发期提示样式
```

### 新增的文件

```
tests/test_wechat_binding.py          # 绑定功能测试套件
docs/phase-a-phone-binding-implementation.md  # 本文档
```

## 使用说明

### 开发期配置（当前默认）

```bash
# 不设置环境变量，或显式设置为 false
export PHONE_BINDING_REQUIRE_SMS=false
```

前后端行为：
- 用户输入手机号后直接进入身份选择
- 小程序显示"开发期免验证码绑定"提示
- 不显示验证码输入框和发送按钮
- 绑定后 `is_phone_verified=false`

### 生产期配置

```bash
# 设置环境变量为 true
export PHONE_BINDING_REQUIRE_SMS=true
```

前后端行为：
- 用户必须输入验证码
- 显示验证码输入框和发送按钮
- 验证码错误无法绑定
- 绑定后 `is_phone_verified=true`

### 小程序配置同步

修改 `miniprogram/config.js`：

```javascript
phoneBindingRequireSms: true  // 改为 true
```

## 未来工作

根据交接文档，接下来的任务是：

1. **阶段 B：课堂工具 Web 页面接入**
   - 将旧课堂工具迁移到 `/teacher/classroom`
   - 教师权限控制
   - localStorage 版本先运行

2. **阶段 C：课堂工具服务化**
   - 设计课堂会话和抽取记录表
   - 接入班级、学生、题库数据
   - API 开发

3. **阶段 D：三模块打通**
   - 统计联动
   - 数据分析

## 技术决策记录

### 为什么 schema 允许空 code？

- Pydantic 在请求到达接口前就会验证
- 如果 schema 强制 `min_length=6`，空验证码会被直接拒绝
- 修改为 `default=""` 允许字段为空，业务逻辑在接口层判断

### 为什么不删除验证码相关代码？

- 文档明确要求："不要删除短信验证码逻辑"
- 保留代码便于后续快速切换到生产模式
- 验证码生成逻辑仍在运行（虽然开发期不发送）

### 为什么前后端都有配置？

- 后端配置控制业务逻辑（是否校验验证码）
- 前端配置控制 UI 显示（是否显示输入框）
- 两者需保持一致，避免用户体验混乱

## 测试命令

```bash
# 语法检查
python -m compileall -q app tests

# 应用导入检查
python -c "from app.main import app; print('import ok')"

# 运行绑定测试
python -m pytest tests/test_wechat_binding.py -v --tb=short

# 运行全量测试（可选，耗时较长）
$env:PYTHONIOENCODING='utf-8'; python -m pytest tests/ -q --tb=short --disable-warnings --maxfail=1
```

## 交接建议

给下一位开发者（codex 或其他工具）的提示：

1. ✅ 阶段 A 已完成，无需重做绑定开关
2. 📍 当前位置：准备开始阶段 B（课堂工具接入）
3. 📂 旧课堂工具位置：`C:\Users\Windows 10\Desktop\ClassRoom-v1(1)\apps\copy-of-classroom-companion-(课堂伴侣)\抽取优化版 2.html`
4. 🎯 下一步目标：创建 `/teacher/classroom` 路由和模板
5. ⚠️ 注意事项：
   - 当前工作区有未提交改动，不要回滚
   - 遵循项目现有模式小步修改
   - 每步都配测试和验证命令
   - 不要重写小程序，不要删除已有逻辑

## 变更影响分析

### 向后兼容性

✅ 完全兼容：
- 现有用户数据不受影响
- 配置切换不影响已绑定用户
- API 接口签名未变

### 风险评估

🟡 低风险：
- 开发期免验证码带来手机号真实性问题
- 已通过 `is_phone_verified=false` 标记区分
- 后续短信服务接入后可升级验证状态

### 回滚方案

如需回滚到原有强制验证码模式：

```bash
export PHONE_BINDING_REQUIRE_SMS=true
```

修改 `miniprogram/config.js`：

```javascript
phoneBindingRequireSms: true
```

无需修改代码，配置切换即可。

---

**文档版本：** 1.0  
**最后更新：** 2026-06-10  
**实施者：** Claude (Kiro)  
**审核状态：** 待审核
