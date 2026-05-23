Content:

markdown


# 管理员后台运营工具增强设计文档
**项目**: 付刷 (Fushua)  
**功能**: 管理员后台运营工具增强  
**设计日期**: 2026-05-22  
**状态**: 设计阶段
---
## 1. 概述
### 1.1 目标
为管理员提供完整的运营能力，能够在生产环境中高效管理用户和系统，而无需直接操作数据库。
### 1.2 功能范围
本次增强包含以下核心功能：
1. **用户详情页** - 查看用户完整信息和统计数据
2. **用户删除** - 安全删除用户及关联数据
3. **批量清理** - 清理测试账号和无效数据
4. **系统公告** - 发布和管理全站公告
5. **数据导出** - 导出用户、班级、题目等数据
### 1.3 设计原则
- **安全第一**: 所有危险操作需要二次确认
- **可追溯**: 所有操作记录审计日志
- **用户友好**: 提供清晰的预览和反馈
- **性能考虑**: 大数据量操作有限制和分页
---
## 2. 技术架构
### 2.1 路由结构
扩展现有 `/admin` 路由，新增以下端点：
/admin/users/{user_id} # 用户详情页 /admin/users/{user_id}/delete # 删除用户 /admin/cleanup # 批量清理页面 /admin/cleanup/execute # 执行清理 /admin/announcements # 公告管理 /admin/announcements/create # 创建公告 /admin/announcements/{id}/edit # 编辑公告 /admin/announcements/{id}/delete # 删除公告 /admin/data-export # 数据导出页面 /admin/data-export/users # 导出用户 /admin/data-export/classes # 导出班级 /admin/data-export/questions # 导出题目 /admin/data-export/stats # 导出统计



### 2.2 权限控制
- 所有路由使用 `require_admin()` 验证
- 删除操作额外检查：不能删除自己、不能删除最后一个管理员
- 批量操作限制单次处理数量（最多100条）
### 2.3 数据模型
需要新增 `Announcement` 表：
```python
class Announcement(Base):
    __tablename__ = "announcements"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    type = Column(String(20), default="info")  # info, warning, success, error
    target_role = Column(String(20), default="all")  # all, student, teacher
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # 数字越大优先级越高
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=True)  # 过期时间，null表示永久
3. 功能详细设计
3.1 用户详情页
路由: /admin/users/{user_id}

显示信息:

基本信息区
用户名、显示名、角色
注册时间、账号状态（正常/禁用/游客/过期）
手机号、微信绑定状态
班级信息区（学生）
所属班级名称
班级教师
加入时间
教学信息区（教师）
创建的班级列表（数量 + 链接）
创建的题库数量
创建的题目数量
创建的作业数量
学习统计区（学生）
总答题数
正确率
完成的作业数
错题数量
收藏题目数
操作历史区
最近10条审计日志（该用户作为操作者）
最近10条被操作记录（该用户作为目标）
操作按钮:

重置密码（已有）
禁用/启用（已有）
删除用户（新增，红色警告样式）
查看详细日志（跳转到审计日志页面并筛选该用户）
实现要点:

使用卡片式布局，信息分区清晰
统计数据使用数字徽章显示
操作按钮固定在页面顶部
危险操作使用红色按钮并二次确认
3.2 用户删除功能
路由: POST /admin/users/{user_id}/delete

级联删除策略:

学生账号
删除所有个人数据：

records - 答题记录
favorites - 收藏
study_plans - 学习计划
class_members - 班级成员关系
notifications - 通知
mastery_records - 掌握记录
教师账号
方案A（推荐）: 禁止删除有数据的教师

检查是否有创建的班级、题库、题目、作业
如果有，返回错误提示，要求先处理这些资源
只允许删除无任何创建资源的教师账号
方案B（备选）: 级联删除所有资源

删除创建的班级（及班级成员）
删除创建的题库和题目
删除创建的作业
⚠️ 危险操作，需要额外确认
审计日志
保留所有审计日志记录
actor_id 字段保留但用户已不存在
显示时标记为"已删除用户"
安全措施:

不能删除自己
不能删除最后一个管理员
删除前显示确认对话框，包含：
用户名
关联数据数量
不可撤销警告
教师删除额外显示：
将影响的班级数量
将影响的学生数量
记录详细的审计日志
审计日志:

python


AuditLog(
    actor_id=admin_user.id,
    action="delete_user",
    target_type="user",
    target_id=user_id,
    detail=f"删除用户 {user.username}，角色：{user.role}，关联数据：{data_summary}"
)
3.3 批量清理功能
路由: /admin/cleanup

清理类型:

1. 测试账号清理
识别规则:

用户名包含 "test"、"测试"、"demo" 等关键词
或：注册时间在指定日期之前且无任何活动记录
安全检查:

不删除有班级的账号
不删除有答题记录的账号
不删除教师账号
实现:

python


test_keywords = ["test", "测试", "demo", "试用"]
query = db.query(User).filter(
    User.role == "student",
    or_(*[User.username.contains(kw) for kw in test_keywords])
)
# 进一步过滤：无班级、无答题记录
2. 过期游客清理
当前功能（已有，保留）:

清理 guest_expires_at < now() 的游客
同时删除 class_members 记录
3. 无效数据清理
清理内容:

孤立的班级成员记录（user_id 不存在）
孤立的答题记录（question_id 不存在）
空题库（没有题目的题库）
未完成的作业（创建超过30天且无人完成）
实现示例:

python


# 孤立的班级成员
orphaned_members = db.query(ClassMember).filter(
    ~ClassMember.user_id.in_(db.query(User.id))
).all()
# 空题库
empty_banks = db.query(QuestionBank).filter(
    ~QuestionBank.id.in_(
        db.query(Question.bank_id).filter(Question.bank_id != None)
    )
).all()
清理流程:

选择清理类型
显示预览（将被清理的数据统计和列表）
用户确认（需要勾选确认框或输入"确认"）
执行清理
记录审计日志
显示清理结果
UI设计:

标签页切换不同清理类型
预览表格显示将被清理的数据
清理按钮默认禁用，勾选确认框后启用
显示不可撤销警告
审计日志:

python


AuditLog(
    actor_id=admin_user.id,
    action="batch_cleanup",
    target_type="system",
    detail=f"批量清理：{cleanup_type}，清理数量：{count}"
)
3.4 系统公告管理
路由: /admin/announcements

功能列表:

创建公告
编辑公告
启用/禁用公告
删除公告
公告列表
公告属性:

标题: 最多200字符
内容: 文本内容，支持换行
类型: info（信息）、warning（警告）、success（成功）、error（错误）
目标角色: all（全部）、student（学生）、teacher（教师）
优先级: 数字，越大越靠前
过期时间: 可选，null表示永久有效
显示位置:

学生首页顶部（显示 target_role=all 或 student 的公告）
教师首页顶部（显示 target_role=all 或 teacher 的公告）
按优先级排序，最多显示3条
可关闭（使用 session 记录已关闭的公告ID）
公告类型样式:

info: 蓝色背景 (#e3f2fd)
warning: 黄色背景 (#fff3e0)
success: 绿色背景 (#e8f5e9)
error: 红色背景 (#ffebee)
管理页面UI:

列表显示所有公告
状态用颜色标识（启用/禁用）
创建/编辑使用表单
实时预览公告显示效果
优先级使用数字输入框
实现要点:

python


# 获取当前有效公告
def get_active_announcements(role: str):
    now = datetime.now()
    return db.query(Announcement).filter(
        Announcement.is_active == True,
        or_(
            Announcement.target_role == "all",
            Announcement.target_role == role
        ),
        or_(
            Announcement.expires_at == None,
            Announcement.expires_at > now
        )
    ).order_by(Announcement.priority.desc()).limit(3).all()
审计日志:

create_announcement - 创建公告
edit_announcement - 编辑公告
delete_announcement - 删除公告
toggle_announcement - 启用/禁用公告
3.5 数据导出功能
路由: /admin/data-export

导出类型:

1. 用户数据导出
筛选条件:

角色：全部/学生/教师/管理员
注册时间范围
账号状态：全部/正常/禁用/游客
导出字段:

用户名
显示名
角色
所属班级（学生）
注册时间
账号状态
手机号（可选）
实现:

python


query = db.query(User)
if role_filter:
    query = query.filter(User.role == role_filter)
if start_date:
    query = query.filter(User.created_at >= start_date)
if end_date:
    query = query.filter(User.created_at <= end_date)
users = query.limit(5000).all()
2. 班级数据导出
筛选条件:

创建教师
创建时间范围
导出字段:

班级名称
创建教师
成员数量
创建时间
可选: 导出班级成员明细

班级名
学生姓名
加入时间
3. 题目数据导出
筛选条件:

科目
学期
题库
创建教师
导出字段:

科目、学期、章节
题型、难度
题目内容
选项A/B/C/D
答案、解析
创建者、创建时间
格式: CSV（与导入格式兼容）

4. 统计数据导出
全站统计:

用户数、班级数、题目数、答题记录数
按日期统计
活跃度统计:

每日活跃用户数
每日答题数
每日新增用户数
导出格式: CSV (UTF-8 with BOM)

CSV格式说明:

python


import csv
import io
buf = io.StringIO()
writer = csv.writer(buf)
writer.writerow(["用户名", "显示名", "角色", "注册时间"])
for user in users:
    writer.writerow([user.username, user.display_name, user.role, user.created_at])
buf.seek(0)
output = buf.getvalue().encode("utf-8-sig")  # BOM for Excel
限制:

单次导出最多5000条记录
超过限制提示分批导出或添加筛选条件
显示预计导出数量
UI设计:

表单式筛选条件
实时显示预计导出数量
导出按钮显示文件大小预估
导出历史记录（最近10次）
审计日志:

python


AuditLog(
    actor_id=admin_user.id,
    action="export_data",
    target_type="system",
    detail=f"导出数据：{export_type}，筛选条件：{filters}，记录数：{count}"
)
4. 安全设计
4.1 权限验证
所有新增路由使用 require_admin():

python


def require_admin(request: Request, db: Session):
    user_id = require_admin_role(request, db)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user
4.2 CSRF保护
所有 POST 请求验证 CSRF token:

python


await validate_csrf_async(request)
表单包含隐藏字段:

html


<input type="hidden" name="csrf_token" value="{{ csrf_token }}">
4.3 二次确认
删除用户:

javascript


if (!confirm(`确定要删除用户 ${username} 吗？\n\n关联数据：\n- 答题记录：${record_count} 条\n- 收藏：${favorite_count} 个\n\n此操作不可撤销！`)) {
    return false;
}
批量清理:

html


<input type="checkbox" id="confirm-cleanup" required>
<label for="confirm-cleanup">我已了解此操作不可撤销</label>
<button type="submit" disabled id="cleanup-btn">执行清理</button>
<script>
document.getElementById('confirm-cleanup').addEventListener('change', function() {
    document.getElementById('cleanup-btn').disabled = !this.checked;
});
</script>
删除教师:

javascript


if (!confirm(`警告：删除教师账号将影响：\n- ${class_count} 个班级\n- ${student_count} 名学生\n- ${question_count} 道题目\n\n确定要继续吗？`)) {
    return false;
}
4.4 审计日志
所有操作记录到 audit_logs 表：



操作	action	target_type	detail
查看用户详情	view_user_detail	user	查看用户 {username} 的详情
删除用户	delete_user	user	删除用户 {username}，角色：{role}
批量清理	batch_cleanup	system	批量清理：{type}，数量：{count}
创建公告	create_announcement	announcement	创建公告：{title}
编辑公告	edit_announcement	announcement	编辑公告：{title}
删除公告	delete_announcement	announcement	删除公告：{title}
导出数据	export_data	system	导出：{type}，数量：{count}
4.5 敏感信息保护
导出数据不包含密码哈希
审计日志不记录密码相关信息
用户详情页不显示密码
手机号部分隐藏（可选）
5. 用户界面设计
5.1 导航结构
管理员后台左侧菜单：



管理员后台
├── 概览 (已有)
├── 用户管理 (已有，增加"查看详情"链接)
├── 班级管理 (已有)
├── 数据清理 (新增) ⭐
├── 系统公告 (新增) ⭐
├── 数据导出 (新增) ⭐
├── 审计日志 (已有)
├── 备份管理 (已有)
└── 邀请码管理 (已有)
5.2 用户详情页布局


┌─────────────────────────────────────────┐
│ 用户详情 - {username}                    │
│ [重置密码] [禁用账号] [删除用户]         │
├─────────────────────────────────────────┤
│ 基本信息                                 │
│ 用户名: xxx  显示名: xxx  角色: 学生     │
│ 注册时间: xxx  状态: 正常                │
├─────────────────────────────────────────┤
│ 班级信息                                 │
│ 所属班级: xxx  教师: xxx  加入: xxx      │
├─────────────────────────────────────────┤
│ 学习统计                                 │
│ 总答题: 1234  正确率: 85%  作业: 12      │
│ 错题: 56  收藏: 23                       │
├─────────────────────────────────────────┤
│ 操作历史                                 │
│ [最近10条审计日志]                       │
└─────────────────────────────────────────┘
5.3 批量清理页布局


┌─────────────────────────────────────────┐
│ 数据清理                                 │
│ [测试账号] [过期游客] [无效数据]         │
├─────────────────────────────────────────┤
│ 清理预览                                 │
│ 将清理以下数据：                         │
│ ┌─────────────────────────────────────┐ │
│ │ 用户名    角色    注册时间    状态   │ │
│ │ test01   学生    2026-01-01  无活动 │ │
│ │ test02   学生    2026-01-02  无活动 │ │
│ └─────────────────────────────────────┘ │
│                                          │
│ ☐ 我已了解此操作不可撤销                │
│ [执行清理] (禁用状态)                    │
└─────────────────────────────────────────┘
5.4 系统公告管理布局


┌─────────────────────────────────────────┐
│ 系统公告管理                [+ 创建公告] │
├─────────────────────────────────────────┤
│ 公告列表                                 │
│ ┌─────────────────────────────────────┐ │
│ │ 标题          类型  目标  状态  操作 │ │
│ │ 系统维护通知  警告  全部  启用  编辑 │ │
│ │ 新功能上线    信息  教师  启用  编辑 │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
5.5 数据导出页布局


┌─────────────────────────────────────────┐
│ 数据导出                                 │
│ [用户] [班级] [题目] [统计]              │
├─────────────────────────────────────────┤
│ 导出条件                                 │
│ 角色: [全部 ▼]                           │
│ 注册时间: [开始日期] - [结束日期]        │
│ 账号状态: [全部 ▼]                       │
│                                          │
│ 预计导出: 1234 条记录 (~500KB)           │
│ [导出CSV]                                │
├─────────────────────────────────────────┤
│ 导出历史                                 │
│ 2026-05-22 14:30 - 用户数据 (1234条)    │
│ 2026-05-21 10:15 - 班级数据 (56条)      │
└─────────────────────────────────────────┘
5.6 响应式设计
表格在小屏幕上可横向滚动
操作按钮在移动端堆叠显示
确认弹窗适配移动端
使用 Bootstrap 响应式类
6. 实现计划
6.1 数据库迁移
创建 announcements 表：

python


# alembic/versions/xxxx_add_announcements.py
def upgrade():
    op.create_table(
        'announcements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=True),
        sa.Column('target_role', sa.String(length=20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_announcements_id'), 'announcements', ['id'], unique=False)
def downgrade():
    op.drop_index(op.f('ix_announcements_id'), table_name='announcements')
    op.drop_table('announcements')
6.2 开发顺序
阶段1: 用户详情和删除 (预计6小时)

用户详情页路由和模板
统计数据查询
删除用户功能
级联删除逻辑
测试
阶段2: 批量清理 (预计4小时)

清理页面路由和模板
测试账号识别逻辑
无效数据识别逻辑
清理执行和审计
测试
阶段3: 系统公告 (预计5小时)

数据库迁移
公告管理路由和模板
公告显示逻辑
前端显示组件
测试
阶段4: 数据导出 (预计5小时)

导出页面路由和模板
用户导出功能
班级导出功能
题目导出功能
统计导出功能
测试
总计: 约20小时 (2.5天)

6.3 测试计划
单元测试:

用户删除级联逻辑
测试账号识别规则
公告过滤逻辑
CSV导出格式
集成测试:

用户详情页显示
删除用户完整流程
批量清理完整流程
公告创建和显示
数据导出完整流程
手动测试:

UI响应式布局
确认对话框
导出文件在Excel中打开
公告在首页显示
7. 风险和注意事项
7.1 数据安全风险
风险: 误删除重要数据

缓解措施:

所有删除操作需要二次确认
显示详细的影响范围
记录详细的审计日志
建议在操作前进行数据备份
7.2 性能风险
风险: 大数据量导出或清理导致超时

缓解措施:

限制单次操作数量（最多5000条）
添加分页和筛选条件
考虑异步处理大批量操作
7.3 权限风险
风险: 管理员权限过大，误操作影响范围广

缓解措施:

所有操作记录审计日志
关键操作需要二次确认
定期审查审计日志
考虑引入"超级管理员"和"普通管理员"角色
7.4 兼容性风险
风险: CSV导出在不同系统中显示异常

缓解措施:

使用 UTF-8 with BOM 编码
测试在 Windows Excel、Mac Excel、Google Sheets 中打开
提供导出格式说明文档
8. 后续优化方向
8.1 短期优化 (1-2周)
添加用户最后登录时间字段
公告支持富文本编辑
导出支持更多格式（Excel、JSON）
批量操作支持异步处理
8.2 中期优化 (1-2月)
数据统计可视化（图表）
用户行为分析
自动化清理任务（定时任务）
公告模板功能
8.3 长期优化 (3-6月)
角色权限细分（超级管理员、普通管理员）
操作审批流程（重要操作需要二次审批）
数据恢复功能（软删除）*_





19:52