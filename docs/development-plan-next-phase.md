# 付刷项目 - 下一阶段详细开发规划

**规划日期**: 2026-05-11  
**当前版本**: v3.1.0  
**目标版本**: v3.2.0 (安全加固完成版)

---

## 📊 当前状态评估

### ✅ 已完成的安全措施
- [x] 权限helper函数 (teacher_owns_student/bank/class/question)
- [x] 班级成员一致性修复
- [x] 题库删除权限校验
- [x] parse_int输入验证
- [x] 审计日志基础设施
- [x] GitHub Actions CI
- [x] CSRF保护
- [x] 安全响应头
- [x] 登录速率限制

### ⚠️ 发现的关键问题
1. **作业权限隔离不完整** - Assignment已有class_id字段，但学生端未完全隔离
2. **教师查看学生详情权限** - 需要验证teacher_owns_student的使用
3. **作业完成权限** - 学生可能完成其他班级的作业
4. **测试覆盖不完整** - 缺少端到端的权限测试

---

## 🎯 第一阶段：权限隔离完善 (预计3-5天)

### 任务1.1：修复学生作业列表权限隔离

**优先级**: 🔴 P0 (关键)  
**预计时间**: 4小时

#### 问题描述
当前 `app/routers/student.py:39` 中，学生dashboard显示所有作业：
```python
assignments = db.query(Assignment).order_by(Assignment.created_at.desc()).all()
```

#### 实施步骤
1. **修改学生dashboard作业查询** (`app/routers/student.py`)
   ```python
   # 修改前
   assignments = db.query(Assignment).order_by(Assignment.created_at.desc()).all()
   
   # 修改后
   user = db.query(User).filter(User.id == user_id).first()
   if user and user.class_id:
       assignments = db.query(Assignment).filter(
           Assignment.class_id == user.class_id
       ).order_by(Assignment.created_at.desc()).all()
   else:
       assignments = []
   ```

2. **修改学生作业列表页面** (`app/routers/student.py` - assignments路由)
   - 查找所有显示作业的路由
   - 添加class_id过滤

3. **验证作业详情页面权限**
   - 检查 `/student/assignments/{assignment_id}` 路由
   - 确保学生只能查看自己班级的作业

#### 测试用例
创建 `tests/test_assignment_isolation.py`:
```python
def test_student_only_sees_own_class_assignments(client, db):
    """学生只能看到自己班级的作业"""
    # 创建两个班级和两个学生
    # 每个班级创建一个作业
    # 验证学生A只能看到班级A的作业

def test_student_cannot_view_other_class_assignment_detail(client, db):
    """学生不能查看其他班级作业详情"""
    # 学生A尝试访问班级B的作业详情
    # 应返回403或404

def test_student_without_class_sees_no_assignments(client, db):
    """没有班级的学生看不到任何作业"""
```

#### 验收标准
- [ ] 学生dashboard只显示本班作业
- [ ] 学生不能通过URL访问其他班级作业
- [ ] 没有班级的学生看到空列表
- [ ] 所有测试通过

---

### 任务1.2：修复作业完成权限校验

**优先级**: 🔴 P0 (关键)  
**预计时间**: 3小时

#### 问题描述
需要验证学生提交作业时，是否属于该作业的班级。

#### 实施步骤
1. **查找作业提交路由** (`app/routers/assignment.py` 或 `app/routers/student.py`)
   ```bash
   grep -n "assignment.*submit\|complete" app/routers/*.py
   ```

2. **添加权限验证**
   ```python
   # 在作业提交处理函数中添加
   assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
   if not assignment:
       raise HTTPException(status_code=404, detail="作业不存在")
   
   user = db.query(User).filter(User.id == user_id).first()
   if assignment.class_id and user.class_id != assignment.class_id:
       raise HTTPException(status_code=403, detail="无权完成此作业")
   ```

3. **处理无班级作业的情况**
   - 如果 `assignment.class_id` 为 None，决定是否允许所有学生完成
   - 建议：要求所有作业必须绑定班级

#### 测试用例
添加到 `tests/test_assignment_isolation.py`:
```python
def test_student_cannot_submit_other_class_assignment(client, db):
    """学生不能提交其他班级的作业"""
    
def test_student_can_submit_own_class_assignment(client, db):
    """学生可以提交自己班级的作业"""
    
def test_assignment_without_class_id_handling(client, db):
    """测试没有class_id的作业的处理逻辑"""
```

#### 验收标准
- [ ] 学生只能提交本班作业
- [ ] 伪造assignment_id无法提交
- [ ] 返回清晰的错误信息
- [ ] 所有测试通过

---

### 任务1.3：验证教师查看学生详情权限

**优先级**: 🔴 P0 (关键)  
**预计时间**: 4小时

#### 问题描述
需要确保教师只能查看自己班级学生的详情和导出PDF。

#### 实施步骤
1. **审查学生详情路由** (`app/routers/teacher.py`)
   ```bash
   grep -n "students/{student_id}\|student_detail" app/routers/teacher.py
   ```

2. **添加权限验证**
   ```python
   from app.routers.permissions import teacher_owns_student
   
   @router.get("/students/{student_id}")
   def student_detail(request: Request, student_id: int, db: Session = Depends(get_db)):
       teacher_id = require_teacher(request, db)
       
       # 添加权限检查
       if not teacher_owns_student(db, teacher_id, student_id):
           raise HTTPException(status_code=404, detail="学生不存在")
       
       student = db.query(User).filter(User.id == student_id).first()
       # ... 其余逻辑
   ```

3. **检查所有学生相关路由**
   - `/teacher/students/{student_id}` - 学生详情
   - `/teacher/students/{student_id}/export/pdf` - PDF导出
   - `/teacher/students/{student_id}/records` - 答题记录
   - 任何其他访问学生数据的路由

4. **统计数据范围限制**
   - 确保教师统计只包含自己班级的学生
   - 班级统计只显示该教师创建的班级

#### 测试用例
创建 `tests/test_teacher_student_permission.py`:
```python
def test_teacher_can_view_own_class_student(client, db):
    """教师可以查看自己班级的学生"""
    
def test_teacher_cannot_view_other_class_student(client, db):
    """教师不能查看其他班级的学生"""
    
def test_teacher_cannot_export_other_class_student_pdf(client, db):
    """教师不能导出其他班级学生的PDF"""
    
def test_teacher_stats_only_include_own_students(client, db):
    """教师统计只包含自己的学生"""
```

#### 验收标准
- [ ] 教师只能查看自己班级学生
- [ ] 猜测student_id无法访问其他学生
- [ ] PDF导出有权限检查
- [ ] 统计数据正确隔离
- [ ] 所有测试通过

---

### 任务1.4：强制作业绑定班级

**优先级**: 🟡 P1 (重要)  
**预计时间**: 3小时

#### 问题描述
当前作业创建时class_id是可选的，应该强制要求。

#### 实施步骤
1. **修改作业创建表单** (`app/templates/teacher/assignment_form.html`)
   ```html
   <select name="class_id" required>
       <option value="">请选择班级</option>
       {% for cls in classes %}
       <option value="{{ cls.id }}">{{ cls.name }}</option>
       {% endfor %}
   </select>
   ```

2. **修改后端验证** (`app/routers/assignment.py:40-100`)
   ```python
   class_id = form.get("class_id", "")
   if not class_id:
       return error_response("请选择班级")
   
   class_id_value = parse_int(class_id, min_value=1)
   if class_id_value is None:
       raise HTTPException(status_code=400, detail="Invalid class id")
   
   if not teacher_owns_class(db, user_id, class_id_value):
       raise HTTPException(status_code=403, detail="班级不存在")
   
   assignment.class_id = class_id_value  # 必填
   ```

3. **数据库迁移** (可选 - 如果要设置NOT NULL)
   ```python
   # alembic/versions/20260511_assignment_class_required.py
   def upgrade():
       # 先给现有作业设置默认class_id
       op.execute("UPDATE assignments SET class_id = (SELECT id FROM class_groups LIMIT 1) WHERE class_id IS NULL")
       # 然后设置NOT NULL约束
       op.alter_column('assignments', 'class_id', nullable=False)
   ```

#### 测试用例
```python
def test_create_assignment_requires_class_id(client, db):
    """创建作业必须指定班级"""
    
def test_create_assignment_validates_class_ownership(client, db):
    """创建作业时验证班级归属"""
```

#### 验收标准
- [ ] 前端表单class_id为必填
- [ ] 后端验证class_id存在且归属正确
- [ ] 所有新作业都有class_id
- [ ] 所有测试通过

---

### 任务1.5：补充端到端权限测试

**优先级**: 🟡 P1 (重要)  
**预计时间**: 6小时

#### 测试场景设计

创建 `tests/test_e2e_permissions.py`:

```python
"""端到端权限测试 - 模拟真实多教师多班级场景"""

def test_complete_isolation_scenario(client, db):
    """完整的数据隔离场景测试"""
    # 场景设置
    # - 教师A创建班级A，添加学生A1, A2
    # - 教师B创建班级B，添加学生B1, B2
    # - 教师A创建题库A，添加题目
    # - 教师B创建题库B，添加题目
    # - 教师A创建作业A（班级A，题库A的题）
    # - 教师B创建作业B（班级B，题库B的题）
    
    # 验证点
    # 1. 教师A不能查看学生B1
    # 2. 教师A不能查看题库B
    # 3. 教师A不能查看作业B
    # 4. 学生A1只能看到作业A
    # 5. 学生A1不能完成作业B
    # 6. 学生B1只能看到作业B
    # 7. 教师A的统计只包含班级A的数据
    # 8. 教师B的统计只包含班级B的数据

def test_cross_teacher_attack_scenarios(client, db):
    """跨教师攻击场景测试"""
    # 测试各种越权尝试
    # - 猜测其他教师的student_id
    # - 猜测其他教师的bank_id
    # - 猜测其他教师的assignment_id
    # - 猜测其他教师的class_id
```

#### 验收标准
- [ ] 完整场景测试通过
- [ ] 所有越权尝试被正确拒绝
- [ ] 测试覆盖率 > 80%

---

## 🎯 第二阶段：数据一致性和边界情况 (预计2-3天)

### 任务2.1：处理学生无班级的情况

**优先级**: 🟡 P1  
**预计时间**: 2小时

#### 实施步骤
1. 审查所有依赖 `user.class_id` 的代码
2. 添加空值检查
3. 提供友好的提示信息

#### 涉及文件
- `app/routers/student.py` - dashboard, assignments
- `app/templates/student/*.html` - 显示提示

---

### 任务2.2：处理作业删除的级联影响

**优先级**: 🟢 P2  
**预计时间**: 2小时

#### 实施步骤
1. 检查删除作业时是否清理 `AssignmentRecord`
2. 添加软删除或级联删除
3. 添加删除确认

---

### 任务2.3：管理员权限例外处理

**优先级**: 🟢 P2  
**预计时间**: 3小时

#### 实施步骤
1. 决定管理员是否可以跨班级查看数据
2. 如果允许，修改权限helper函数
3. 添加审计日志记录管理员操作

```python
def teacher_owns_student(db: Session, teacher_id: int, student_id: int) -> bool:
    """检查学生是否属于该教师创建的班级"""
    # 检查是否是管理员
    teacher = db.query(User).filter(User.id == teacher_id).first()
    if teacher and teacher.role == "admin":
        return True  # 管理员可以查看所有学生
    
    # 原有逻辑
    teacher_classes = select(ClassGroup.id).where(ClassGroup.created_by == teacher_id)
    return db.query(ClassMember).filter(
        ClassMember.class_id.in_(teacher_classes),
        ClassMember.user_id == student_id,
    ).first() is not None
```

---

## 🎯 第三阶段：运维和监控增强 (预计2-3天)

### 任务3.1：增强审计日志

**优先级**: 🟡 P1  
**预计时间**: 4小时

#### 需要记录的操作
- 教师查看其他班级学生（如果是管理员）
- 作业创建、修改、删除
- 学生移出班级
- 题库删除
- 批量导入操作

#### 实施步骤
1. 在关键操作点添加审计日志
2. 创建审计日志查询页面
3. 添加日志导出功能

---

### 任务3.2：数据库备份脚本

**优先级**: 🟡 P1  
**预计时间**: 3小时

#### 实施步骤
1. 创建备份脚本 `scripts/backup_db.sh`
2. 创建恢复脚本 `scripts/restore_db.sh`
3. 编写备份文档 `docs/backup-and-restore.md`
4. 配置定期备份（Render或cron）

---

### 任务3.3：监控和告警

**优先级**: 🟢 P2  
**预计时间**: 4小时

#### 实施步骤
1. 增强 `/health` 端点
2. 添加关键指标监控
3. 配置Render告警
4. 可选：接入Sentry

---

## 🎯 第四阶段：用户体验优化 (预计2-3天)

### 任务4.1：错误信息优化

**优先级**: 🟢 P2  
**预计时间**: 2小时

#### 实施步骤
1. 统一错误信息格式
2. 提供用户友好的错误提示
3. 避免泄露敏感信息

---

### 任务4.2：性能优化 - 添加分页

**优先级**: 🟢 P2  
**预计时间**: 4小时

#### 需要分页的页面
- 题库管理
- 学生管理
- 答题记录
- 作业列表

---

## 📋 执行时间表

### Week 1 (Day 1-5)
- **Day 1-2**: 任务1.1, 1.2 (作业权限隔离)
- **Day 3**: 任务1.3 (教师查看学生权限)
- **Day 4**: 任务1.4 (强制作业绑定班级)
- **Day 5**: 任务1.5 (端到端测试)

### Week 2 (Day 6-10)
- **Day 6**: 任务2.1, 2.2 (边界情况处理)
- **Day 7**: 任务2.3 (管理员权限)
- **Day 8**: 任务3.1 (审计日志增强)
- **Day 9**: 任务3.2 (数据库备份)
- **Day 10**: 任务3.3 (监控告警)

### Week 3 (Day 11-12)
- **Day 11**: 任务4.1, 4.2 (用户体验优化)
- **Day 12**: 回归测试、文档更新、发布准备

---

## ✅ 验收标准

### 功能验收
- [ ] 所有P0任务完成
- [ ] 所有自动化测试通过
- [ ] 测试覆盖率 > 80%
- [ ] 无已知的P0/P1 bug

### 安全验收
- [ ] 教师不能查看其他教师的数据
- [ ] 学生不能查看其他班级的数据
- [ ] 学生不能完成其他班级的作业
- [ ] 所有权限测试通过

### 性能验收
- [ ] 页面加载时间 < 2秒
- [ ] 数据库查询优化
- [ ] 无N+1查询问题

### 文档验收
- [ ] API文档更新
- [ ] 部署文档更新
- [ ] 备份恢复文档完成
- [ ] 测试文档完成

---

## 🚀 发布计划

### v3.2.0-beta (Week 1结束)
- 完成所有P0任务
- 内部测试

### v3.2.0-rc (Week 2结束)
- 完成所有P1任务
- 小范围灰度测试

### v3.2.0 (Week 3结束)
- 完成所有任务
- 正式发布

---

## 📊 风险评估

### 高风险
- **数据迁移失败**: 如果修改数据库schema，需要仔细测试迁移
- **权限逻辑错误**: 可能导致数据泄露或功能不可用

### 中风险
- **性能下降**: 添加权限检查可能影响性能
- **测试覆盖不足**: 可能遗漏边界情况

### 缓解措施
- 在测试环境充分测试
- 保持数据库备份
- 分阶段发布
- 保留回滚方案

---

## 📝 开发规范

### 代码规范
- 所有权限检查使用helper函数
- 所有数字输入使用parse_int
- 所有用户输入使用sanitize_input
- 所有POST请求验证CSRF

### 测试规范
- 每个功能至少3个测试用例（正常、异常、边界）
- 所有权限功能必须有测试
- 测试命名清晰描述测试场景

### 提交规范
- feat: 新功能
- fix: bug修复
- test: 测试相关
- docs: 文档更新
- refactor: 重构

---

## 🔗 相关文档

- [产品成熟化路线图](./product-maturity-roadmap.md)
- [v3.1.0发布计划](./superpowers/plans/2026-05-08-fushua-production-release.md)
- [权限隔离计划](./superpowers/plans/2026-05-09-fushua-v5-permission-isolation.md)

---

**最后更新**: 2026-05-11  
**负责人**: 开发团队  
**审核人**: 待定
