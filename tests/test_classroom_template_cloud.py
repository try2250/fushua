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


def test_classroom_react_babel_script_is_not_nested_inside_plain_script():
    html = Path("app/templates/teacher/classroom.html").read_text(encoding="utf-8")
    app_script_area = html[html.index('<div id="root"></div>'):]

    assert '<script>\n<!-- {% raw %} -->\n<script type="text/babel">' not in app_script_area
    assert "Babel.registerPreset('classroom-react-classic'" in html
    assert app_script_area.count('<script type="text/babel" data-presets="classroom-react-classic">') == 1


def test_classroom_babel_script_avoids_browser_module_imports():
    html = Path("app/templates/teacher/classroom.html").read_text(encoding="utf-8")
    app_script_area = html[html.index('<script type="text/babel"'):]

    assert "runtime: 'classic'" in html
    assert "from 'react/jsx-runtime'" not in app_script_area
    assert 'from "react/jsx-runtime"' not in app_script_area


def test_classroom_cloud_students_include_runtime_history_array():
    html = Path("app/templates/teacher/classroom.html").read_text(encoding="utf-8")

    assert "name: s.display_name || s.username,\n                                classId: activeClassId,\n                                score: 0,\n                                history: []" in html


def test_classroom_bootstrap_restores_api_current_session_id():
    html = Path("app/templates/teacher/classroom.html").read_text(encoding="utf-8")

    assert "ClassroomAPI.currentSessionId = boot.active_session.id" in html


def test_classroom_bootstrap_prefers_active_session_class():
    html = Path("app/templates/teacher/classroom.html").read_text(encoding="utf-8")

    assert "boot.active_session && boot.active_session.class_id" in html
    assert "const activeClassId = boot.active_session && boot.active_session.class_id" in html


def test_classroom_entering_session_view_creates_cloud_session():
    html = Path("app/templates/teacher/classroom.html").read_text(encoding="utf-8")

    assert "const ensureActiveSession = async ()" in html
    assert "ClassroomAPI.createSession(state.activeClassId" in html
    assert "setView={handleSetView}" in html
    assert "Dashboard state={state} setView={handleSetView}" in html


def test_classroom_layout_exposes_cockpit_status_controls():
    html = Path("app/templates/teacher/classroom.html").read_text(encoding="utf-8")

    for label in ["课堂状态", "云端保存", "结束课堂", "当前班级"]:
        assert label in html
    assert "activeSession={state.activeSession}" in html
    assert "cloudStatus={cloudStatus}" in html
    assert "onFinishSession={handleFinishSession}" in html


def test_classroom_finish_session_clears_cloud_session():
    html = Path("app/templates/teacher/classroom.html").read_text(encoding="utf-8")

    assert "const handleFinishSession = async ()" in html
    assert "ClassroomAPI.finishSession(ClassroomAPI.currentSessionId)" in html
    assert "ClassroomAPI.currentSessionId = null" in html
    assert "activeSession: null" in html
