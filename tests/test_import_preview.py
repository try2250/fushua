import pytest
import json
import re
from tests.conftest import create_test_user, register_and_login, get_csrf_token
from app.models import Question, QuestionBank
from app.routers.teacher import _pending_imports


def _extract_token(text):
    match = re.search(r'name="import_token"\s+value="([^"]+)"', text)
    return match.group(1) if match else ""


CSV_HEADER = "subject,semester,chapter,q_type,difficulty,content,option_a,option_b,option_c,option_d,answer,explanation"


class TestImportPreviewPage:
    def test_import_page_uses_preview_action(self, client, db_session):
        teacher = create_test_user(db_session, "previewteacher1", "teacher")
        register_and_login(client, "previewteacher1", "teacher")
        response = client.get("/teacher/questions/import")
        assert response.status_code == 200
        assert "import-preview" in response.text
        assert "预览导入" in response.text

    def test_preview_csv_valid_file(self, client, db_session):
        teacher = create_test_user(db_session, "previewteacher2", "teacher")
        register_and_login(client, "previewteacher2", "teacher")
        csrf = get_csrf_token(client)
        csv_content = CSV_HEADER + "\n数学,八年级上册,代数,choice,2,1+1等于几？,1,2,3,4,B,1+1=2\n英语,七年级上册,,fill,1,Apple的中文意思是___,,,,,苹果,"
        response = client.post(
            "/teacher/questions/import-preview",
            data={"_csrf_token": csrf, "bank_id": ""},
            files={"file": ("test.csv", csv_content.encode("utf-8"), "text/csv")},
        )
        assert response.status_code == 200
        assert "导入预览" in response.text

    def test_preview_json_valid_file(self, client, db_session):
        teacher = create_test_user(db_session, "previewteacher3", "teacher")
        register_and_login(client, "previewteacher3", "teacher")
        csrf = get_csrf_token(client)
        json_content = json.dumps([
            {"subject": "数学", "content": "1+1等于几？", "answer": "2", "q_type": "fill"},
            {"subject": "英语", "content": "Apple的中文意思是___", "answer": "苹果", "q_type": "fill"},
        ], ensure_ascii=False)
        response = client.post(
            "/teacher/questions/import-preview",
            data={"_csrf_token": csrf, "bank_id": ""},
            files={"file": ("test.json", json_content.encode("utf-8"), "application/json")},
        )
        assert response.status_code == 200
        assert "导入预览" in response.text

    def test_preview_detects_error_rows(self, client, db_session):
        teacher = create_test_user(db_session, "previewteacher4", "teacher")
        register_and_login(client, "previewteacher4", "teacher")
        csrf = get_csrf_token(client)
        csv_content = CSV_HEADER + "\n数学,八年级上册,代数,choice,2,1+1等于几？,1,2,3,4,B,1+1=2\n,七年级上册,,fill,1,缺少科目题,,,,,,\n英语,,,,1,光速比声速快,,,,,,"
        response = client.post(
            "/teacher/questions/import-preview",
            data={"_csrf_token": csrf, "bank_id": ""},
            files={"file": ("test.csv", csv_content.encode("utf-8"), "text/csv")},
        )
        assert response.status_code == 200
        assert "错误行" in response.text

    def test_preview_detects_duplicate_in_db(self, client, db_session):
        teacher = create_test_user(db_session, "previewteacher5", "teacher")
        q = Question(
            subject="数学", content="1+1等于几？", answer="B",
            q_type="choice", difficulty=2, created_by=teacher.id,
        )
        db_session.add(q)
        db_session.commit()
        register_and_login(client, "previewteacher5", "teacher")
        csrf = get_csrf_token(client)
        csv_content = CSV_HEADER + "\n数学,八年级上册,代数,choice,2,1+1等于几？,1,2,3,4,B,1+1=2"
        response = client.post(
            "/teacher/questions/import-preview",
            data={"_csrf_token": csrf, "bank_id": ""},
            files={"file": ("test.csv", csv_content.encode("utf-8"), "text/csv")},
        )
        assert response.status_code == 200
        assert "重复题" in response.text

    def test_preview_detects_duplicate_within_file(self, client, db_session):
        teacher = create_test_user(db_session, "previewteacher6", "teacher")
        register_and_login(client, "previewteacher6", "teacher")
        csrf = get_csrf_token(client)
        csv_content = CSV_HEADER + "\n数学,八年级上册,代数,choice,2,1+1等于几？,1,2,3,4,B,1+1=2\n数学,八年级上册,代数,choice,2,1+1等于几？,1,2,3,4,B,1+1=2"
        response = client.post(
            "/teacher/questions/import-preview",
            data={"_csrf_token": csrf, "bank_id": ""},
            files={"file": ("test.csv", csv_content.encode("utf-8"), "text/csv")},
        )
        assert response.status_code == 200
        assert "重复题" in response.text

    def test_preview_rejects_unsupported_format(self, client, db_session):
        teacher = create_test_user(db_session, "previewteacher7", "teacher")
        register_and_login(client, "previewteacher7", "teacher")
        csrf = get_csrf_token(client)
        response = client.post(
            "/teacher/questions/import-preview",
            data={"_csrf_token": csrf, "bank_id": ""},
            files={"file": ("test.txt", b"hello", "text/plain")},
        )
        assert response.status_code == 200
        assert "仅支持 JSON 和 CSV 格式" in response.text

    def test_preview_shows_first_20_rows(self, client, db_session):
        teacher = create_test_user(db_session, "previewteacher8", "teacher")
        register_and_login(client, "previewteacher8", "teacher")
        csrf = get_csrf_token(client)
        rows = []
        for i in range(25):
            rows.append(f"数学,,,choice,2,题目{i},,,,,A,")
        csv_content = CSV_HEADER + "\n" + "\n".join(rows)
        response = client.post(
            "/teacher/questions/import-preview",
            data={"_csrf_token": csrf, "bank_id": ""},
            files={"file": ("test.csv", csv_content.encode("utf-8"), "text/csv")},
        )
        assert response.status_code == 200
        assert "25" in response.text
        assert "仅显示前 20 行" in response.text

    def test_preview_requires_teacher(self, client, db_session):
        create_test_user(db_session, "previewstudent1", "student")
        register_and_login(client, "previewstudent1", "student")
        csrf = get_csrf_token(client)
        csv_content = "subject,content,answer\n数学,测试,A"
        response = client.post(
            "/teacher/questions/import-preview",
            data={"_csrf_token": csrf, "bank_id": ""},
            files={"file": ("test.csv", csv_content.encode("utf-8"), "text/csv")},
        )
        assert response.status_code == 403

    def test_preview_has_confirm_and_cancel(self, client, db_session):
        teacher = create_test_user(db_session, "previewteacher9", "teacher")
        register_and_login(client, "previewteacher9", "teacher")
        csrf = get_csrf_token(client)
        csv_content = CSV_HEADER + "\n数学,八年级上册,代数,choice,2,1+1等于几？,1,2,3,4,B,1+1=2"
        response = client.post(
            "/teacher/questions/import-preview",
            data={"_csrf_token": csrf, "bank_id": ""},
            files={"file": ("test.csv", csv_content.encode("utf-8"), "text/csv")},
        )
        assert response.status_code == 200
        assert "确认导入" in response.text
        assert "取消" in response.text
        assert "import_token" in response.text


class TestImportConfirm:
    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_confirm_imports_questions(self, client, db_session):
        teacher = create_test_user(db_session, "confirmteacher1", "teacher")
        register_and_login(client, "confirmteacher1", "teacher")
        csrf = get_csrf_token(client)
        csv_content = CSV_HEADER + "\n数学,八年级上册,代数,choice,2,1+1等于几？,1,2,3,4,B,1+1=2\n英语,七年级上册,,fill,1,Apple的中文意思是___,,,,,苹果,"
        preview_resp = client.post(
            "/teacher/questions/import-preview",
            data={"_csrf_token": csrf, "bank_id": ""},
            files={"file": ("test.csv", csv_content.encode("utf-8"), "text/csv")},
        )
        assert preview_resp.status_code == 200
        import_token = _extract_token(preview_resp.text)
        assert import_token

        csrf2 = get_csrf_token(client)
        confirm_resp = client.post(
            "/teacher/questions/import-confirm",
            data={"_csrf_token": csrf2, "import_token": import_token},
        )
        assert confirm_resp.status_code == 200
        assert "成功导入 2 道题目" in confirm_resp.text
        questions = db_session.query(Question).filter(Question.created_by == teacher.id).all()
        assert len(questions) == 2

    def test_confirm_with_invalid_token(self, client, db_session):
        teacher = create_test_user(db_session, "confirmteacher2", "teacher")
        register_and_login(client, "confirmteacher2", "teacher")
        csrf = get_csrf_token(client)
        response = client.post(
            "/teacher/questions/import-confirm",
            data={"_csrf_token": csrf, "import_token": "invalid-token"},
        )
        assert response.status_code == 200
        assert "导入会话已过期" in response.text

    def test_confirm_with_wrong_user(self, client, db_session):
        teacher1 = create_test_user(db_session, "confirmteacher3", "teacher")
        teacher2 = create_test_user(db_session, "confirmteacher4", "teacher")
        register_and_login(client, "confirmteacher3", "teacher")
        csrf = get_csrf_token(client)
        csv_content = CSV_HEADER + "\n数学,八年级上册,代数,choice,2,1+1等于几？,1,2,3,4,B,1+1=2"
        preview_resp = client.post(
            "/teacher/questions/import-preview",
            data={"_csrf_token": csrf, "bank_id": ""},
            files={"file": ("test.csv", csv_content.encode("utf-8"), "text/csv")},
        )
        import_token = _extract_token(preview_resp.text)

        register_and_login(client, "confirmteacher4", "teacher")
        csrf2 = get_csrf_token(client)
        confirm_resp = client.post(
            "/teacher/questions/import-confirm",
            data={"_csrf_token": csrf2, "import_token": import_token},
        )
        assert confirm_resp.status_code == 200
        assert "导入会话已过期" in confirm_resp.text

    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_confirm_with_bank_id(self, client, db_session):
        teacher = create_test_user(db_session, "confirmteacher5", "teacher")
        bank = QuestionBank(name="测试题库", subject="数学", created_by=teacher.id)
        db_session.add(bank)
        db_session.commit()
        register_and_login(client, "confirmteacher5", "teacher")
        csrf = get_csrf_token(client)
        csv_content = CSV_HEADER + "\n数学,八年级上册,代数,choice,2,1+1等于几？,1,2,3,4,B,1+1=2"
        preview_resp = client.post(
            "/teacher/questions/import-preview",
            data={"_csrf_token": csrf, "bank_id": str(bank.id)},
            files={"file": ("test.csv", csv_content.encode("utf-8"), "text/csv")},
        )
        import_token = _extract_token(preview_resp.text)

        csrf2 = get_csrf_token(client)
        confirm_resp = client.post(
            "/teacher/questions/import-confirm",
            data={"_csrf_token": csrf2, "import_token": import_token},
        )
        assert confirm_resp.status_code == 200
        assert "成功导入 1 道题目" in confirm_resp.text
        q = db_session.query(Question).filter(Question.created_by == teacher.id).first()
        assert q.bank_id == bank.id

    def test_confirm_skips_error_and_duplicate_rows(self, client, db_session):
        teacher = create_test_user(db_session, "confirmteacher6", "teacher")
        q = Question(
            subject="数学", content="已有题", answer="A",
            q_type="choice", difficulty=2, created_by=teacher.id,
        )
        db_session.add(q)
        db_session.commit()
        register_and_login(client, "confirmteacher6", "teacher")
        csrf = get_csrf_token(client)
        csv_content = CSV_HEADER + "\n数学,八年级上册,代数,choice,2,新题目,1,2,3,4,B,解析\n,七年级上册,,fill,1,缺少科目题,,,,,,\n数学,,,,2,已有题,,,,,,A,"
        preview_resp = client.post(
            "/teacher/questions/import-preview",
            data={"_csrf_token": csrf, "bank_id": ""},
            files={"file": ("test.csv", csv_content.encode("utf-8"), "text/csv")},
        )
        assert preview_resp.status_code == 200
        assert "错误行" in preview_resp.text
        assert "重复题" in preview_resp.text

        import_token = _extract_token(preview_resp.text)

        csrf2 = get_csrf_token(client)
        confirm_resp = client.post(
            "/teacher/questions/import-confirm",
            data={"_csrf_token": csrf2, "import_token": import_token},
        )
        assert confirm_resp.status_code == 200
        assert "成功导入 1 道题目" in confirm_resp.text

    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_confirm_json_import(self, client, db_session):
        teacher = create_test_user(db_session, "confirmteacher7", "teacher")
        register_and_login(client, "confirmteacher7", "teacher")
        csrf = get_csrf_token(client)
        json_content = json.dumps([
            {"subject": "数学", "content": "1+1等于几？", "answer": "2", "q_type": "fill"},
        ], ensure_ascii=False)
        preview_resp = client.post(
            "/teacher/questions/import-preview",
            data={"_csrf_token": csrf, "bank_id": ""},
            files={"file": ("test.json", json_content.encode("utf-8"), "application/json")},
        )
        import_token = _extract_token(preview_resp.text)

        csrf2 = get_csrf_token(client)
        confirm_resp = client.post(
            "/teacher/questions/import-confirm",
            data={"_csrf_token": csrf2, "import_token": import_token},
        )
        assert confirm_resp.status_code == 200
        assert "成功导入 1 道题目" in confirm_resp.text
        q = db_session.query(Question).filter(Question.created_by == teacher.id).first()
        assert q is not None
        assert q.content == "1+1等于几？"

    def test_confirm_requires_teacher(self, client, db_session):
        create_test_user(db_session, "confirmstudent1", "student")
        register_and_login(client, "confirmstudent1", "student")
        csrf = get_csrf_token(client)
        response = client.post(
            "/teacher/questions/import-confirm",
            data={"_csrf_token": csrf, "import_token": "any-token"},
        )
        assert response.status_code == 403

    def test_preview_no_valid_rows_no_confirm_button(self, client, db_session):
        teacher = create_test_user(db_session, "previewteacher10", "teacher")
        register_and_login(client, "previewteacher10", "teacher")
        csrf = get_csrf_token(client)
        csv_content = CSV_HEADER + "\n,,,,,,1,2,3,4,,\n,,,,,,5,6,7,8,,"
        response = client.post(
            "/teacher/questions/import-preview",
            data={"_csrf_token": csrf, "bank_id": ""},
            files={"file": ("test.csv", csv_content.encode("utf-8"), "text/csv")},
        )
        assert response.status_code == 200
        assert "确认导入" not in response.text
