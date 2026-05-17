# 班级成员一致性修复总结

## 修复日期
2026-05-16

## 问题描述

**风险：** `users.class_id` 与 `class_members` 表可能不一致，导致学生同时属于多个班级或数据不同步。

## 探索发现

### ✅ 已正确实现的流程

1. **注册流程**（formal/apply/guest 三种模式）
   - 正确处理 `class_id` 和 `ClassMember` 的同步写入
   - 位置：`app/routers/auth.py`

2. **手动添加学生**
   - 已有检查：不能添加已在其他班级的学生
   - 位置：`app/routers/classgroup.py` 行 93-97
   - 验证逻辑：
     ```python
     if student.class_id and student.class_id != class_id:
         return error("学生已在其他班级")
     ```

3. **移除学生**
   - 正确清空 `users.class_id`
   - 同时删除 `ClassMember` 记录
   - 位置：`app/routers/classgroup.py`

4. **审批访客/加入请求**
   - 正确设置 `class_id` 和创建 `ClassMember`
   - 位置：`app/routers/teacher.py`

### 🔴 发现的漏洞

**批量导入学生绕过验证**
- **位置：** `app/routers/teacher.py` 行 1710-1722
- **问题：** CSV 导入现有学生时，直接覆盖 `class_id`，不检查学生是否已在其他班级
- **影响：** 教师可以通过批量导入"抢走"其他教师的学生

## 修复内容

### 1. 批量导入添加验证（高优先级）

**文件：** `app/routers/teacher.py` 行 1721-1727

**修复前：**
```python
if existing:
    member = db.query(ClassMember).filter(...).first()
    if not member:
        db.add(ClassMember(class_id=cls.id, user_id=existing.id))
    existing.class_id = cls.id  # ⚠️ 直接覆盖，不检查
```

**修复后：**
```python
if existing:
    # 检查是否已在其他班级
    if existing.class_id and existing.class_id != cls.id:
        skipped_count += 1
        skipped_details.append({
            "username": username,
            "reason": f"已在其他班级（class_id={existing.class_id}）"
        })
        continue
    
    # 原有逻辑：创建 ClassMember 和设置 class_id
    member = db.query(ClassMember).filter(...).first()
    if not member:
        db.add(ClassMember(class_id=cls.id, user_id=existing.id))
    existing.class_id = cls.id
    updated_count += 1
```

**返回结果增强：**
```python
"success": f"导入完成：新建 {created_count} 人，更新 {updated_count} 人，跳过 {skipped_count} 人"
```

### 2. 审批端点添加防御性检查（中优先级）

虽然理论上访客学生的 `class_id` 应该是 `None`，但添加防御性验证增加安全性。

**文件：** `app/routers/teacher.py`

**位置 1：审批访客学生（行 1536-1566）**
```python
# 在设置 class_id 前添加检查
if student.class_id and student.class_id != cls.id:
    return templates.TemplateResponse(request, "teacher/students.html", {
        "error": f"学生 {student.username} 已在其他班级，无法审批"
    })
```

**位置 2：审批加入请求（行 1570-1599）**
```python
# 在设置 class_id 前添加检查
if student.class_id and student.class_id != cls.id:
    return templates.TemplateResponse(request, "teacher/students.html", {
        "error": f"学生 {student.username} 已在其他班级，无法审批"
    })
```

## 测试覆盖

### 新增测试文件

**文件：** `tests/test_bulk_import_consistency.py`

### 测试用例（5个）

#### 1. `test_import_student_already_in_other_class_skips`
- **场景：** 学生 A 在班级 1，教师 B 导入包含学生 A 的 CSV 到班级 2
- **验证：** 学生 A 被跳过，仍在班级 1，返回结果包含跳过信息

#### 2. `test_import_student_without_class_succeeds`
- **场景：** 学生 A 没有班级（`class_id = None`），教师 B 导入包含学生 A 的 CSV
- **验证：** 学生 A 成功加入班级 2

#### 3. `test_import_student_already_in_target_class_idempotent`
- **场景：** 学生 A 已在班级 1，教师 A 再次导入包含学生 A 的 CSV 到班级 1
- **验证：** 操作成功，学生 A 仍在班级 1（幂等）

#### 4. `test_approve_guest_already_in_other_class_fails`
- **场景：** 访客学生 A 的 `class_id` 被意外设置为班级 1，教师 B 尝试审批学生 A 加入班级 2
- **验证：** 审批失败，返回错误信息

#### 5. `test_approve_join_request_already_in_other_class_fails`
- **场景：** 学生 A 提交加入班级 2 的请求，但 `class_id` 被意外设置为班级 1，教师 B 尝试审批
- **验证：** 审批失败，返回错误信息

### 修复的测试

**文件：** `tests/test_bulk_import_consistency.py` 和 `tests/test_student_import.py`

**问题：** 测试使用 `files={"file": ...}` 上传文件，但端点期望 `csv_text` 表单字段

**修复：** 将所有测试改为使用 `data={"csv_text": csv_content, "_csrf_token": csrf}`

**额外修复：** `test_student_import.py::test_import_skips_existing_users`
- 旧期望：`"跳过（已存在） 1 人"`
- 新期望：`"更新 1 人"`（现有学生无 class_id 时会被更新而不是跳过）

## 测试结果

### 新增测试
- 5 个新测试全部通过

### 完整测试套件
- **总测试数：** 440（435 → 440）
- **通过：** 440
- **失败：** 0
- **执行时间：** 184.48 秒

## 一致性保证

修复后的一致性保证：

1. ✅ 学生只能属于一个班级（通过所有入口验证）
2. ✅ `users.class_id` 与 `class_members` 始终同步
3. ✅ 教师无法通过任何方式"抢走"其他教师的学生
4. ✅ 批量导入会跳过已在其他班级的学生，并提供详细信息
5. ✅ 审批端点有防御性检查，防止意外数据状态

## 相关文件

### 修改的文件
- `app/routers/teacher.py` - 批量导入验证和审批端点检查
- `tests/test_bulk_import_consistency.py` - 新增 5 个测试用例
- `tests/test_student_import.py` - 修复测试期望

### 参考文件
- `app/routers/classgroup.py` - 手动添加学生的验证逻辑（参考实现）
- `tests/test_class_membership_consistency.py` - 现有的一致性测试

## 下一步

根据 [产品成熟化路线图](product-maturity-roadmap.md)，下一步推荐：

1. **数据备份自动化**（路线图 Step 2.1）- 生产环境必备
2. **修复高优先级 N+1 查询**（路线图 Step 7.1）- 立即改善用户体验

完成这两项后，项目可进入真实班级灰度试用。
