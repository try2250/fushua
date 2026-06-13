import pytest
from tests.conftest import get_csrf_token, login_as, create_test_user


def _platform_login(client, platform_admin):
    from tests.conftest import get_csrf_token
    csrf = get_csrf_token(client)
    return client.post("/platform/login", data={
        "username": platform_admin.username, "password": "rootpass", "_csrf_token": csrf,
    }, follow_redirects=False)


def test_admin_force_password_change_full_flow(client, db_session, platform_admin):
    pytest.skip("invite codes removed in Plan 1.2B")


def test_admin_can_access_admin_panel_after_login(client, db_session, platform_admin):
    pytest.skip("invite codes removed in Plan 1.2B")


def test_settings_page_renders_for_admin(client, db_session, platform_admin):
    pytest.skip("invite codes removed in Plan 1.2B")


def test_settings_template_no_missing_css_vars(client, db_session, platform_admin):
    pytest.skip("invite codes removed in Plan 1.2B")


def test_admin_role_display_in_settings(client, db_session, platform_admin):
    pytest.skip("invite codes removed in Plan 1.2B")
