"""课堂模板云端唯一化 - 守卫测试"""
from pathlib import Path


BUSINESS_KEYS = [
    "classroom_companion_data_v2",
    "classroom_draw_history_v3",
    "classroom_companion_snapshots_v2",
    "classroom_api_mode",
]


def test_classroom_template_does_not_expose_api_mode_toggle():
    html = Path("app/templates/teacher/classroom.html").read_text(encoding="utf-8")
    assert "apiModeToggle" not in html, "不应再有 API 模式开关"
    assert "迁移历史数据" not in html, "不应再有迁移 UI"
    assert "localStorage 模式" not in html, "不应再有 localStorage 模式文案"


def test_classroom_business_localstorage_keys_removed_from_runtime_files():
    combined = "\n".join([
        Path("app/templates/teacher/classroom.html").read_text(encoding="utf-8"),
        Path("app/static/classroom-api.js").read_text(encoding="utf-8"),
    ])
    for key in BUSINESS_KEYS:
        assert key not in combined, f"业务localStorage key '{key}' 不应出现在运行时文件中"
