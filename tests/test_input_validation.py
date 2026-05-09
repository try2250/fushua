import pytest
from app.utils.validation import parse_int, parse_float


class TestParseInt:
    def test_valid_int_returns_original(self):
        assert parse_int(5) == 5
        assert parse_int(0) == 0
        assert parse_int(-3) == -3
        assert parse_int("10") == 10
        assert parse_int("  42  ") == 42

    def test_invalid_value_returns_default(self):
        assert parse_int("abc") is None
        assert parse_int("12.34") is None
        assert parse_int([1, 2]) is None
        assert parse_int({"key": "value"}) is None

    def test_none_returns_default(self):
        assert parse_int(None) is None
        assert parse_int(None, default=99) == 99

    def test_empty_string_returns_default(self):
        assert parse_int("") is None
        assert parse_int("  ") is None
        assert parse_int("", default=0) == 0

    def test_below_min_value_returns_default(self):
        assert parse_int(3, min_value=5) is None
        assert parse_int(0, min_value=1) is None
        assert parse_int(-5, min_value=0) is None
        assert parse_int(5, min_value=5) == 5

    def test_above_max_value_returns_default(self):
        assert parse_int(100, max_value=10) is None
        assert parse_int(6, max_value=5) is None
        assert parse_int(5, max_value=5) == 5

    def test_with_min_and_max(self):
        assert parse_int(5, min_value=1, max_value=10) == 5
        assert parse_int(0, min_value=1, max_value=10) is None
        assert parse_int(11, min_value=1, max_value=10) is None


class TestParseFloat:
    def test_valid_float_returns_original(self):
        assert parse_float(3.14) == 3.14
        assert parse_float(0.0) == 0.0
        assert parse_float(-1.5) == -1.5
        assert parse_float("2.5") == 2.5
        assert parse_float("  1.23  ") == 1.23
        assert parse_float("10") == 10.0

    def test_invalid_value_returns_default(self):
        assert parse_float("abc") is None
        assert parse_float([1, 2]) is None
        assert parse_float({"key": "value"}) is None

    def test_none_returns_default(self):
        assert parse_float(None) is None
        assert parse_float(None, default=1.5) == 1.5

    def test_empty_string_returns_default(self):
        assert parse_float("") is None
        assert parse_float("  ") is None
        assert parse_float("", default=0.0) == 0.0

    def test_below_min_value_returns_default(self):
        assert parse_float(1.0, min_value=5.0) is None
        assert parse_float(0.5, min_value=1.0) is None

    def test_above_max_value_returns_default(self):
        assert parse_float(100.0, max_value=10.0) is None
        assert parse_float(6.5, max_value=5.0) is None


class TestRouteInvalidInputs:
    def test_invalid_difficulty_no_500(self, client, db_session):
        response = client.get("/student/practice?difficulty=invalid")
        assert response.status_code != 500

    def test_invalid_count_no_500(self, client, db_session):
        response = client.get("/student/practice?count=abc")
        assert response.status_code != 500

    def test_invalid_daily_goal_no_500(self, client, db_session):
        from tests.conftest import create_test_user
        create_test_user(db_session)
        login_as = __import__("tests.conftest", fromlist=["login_as"]).login_as
        login_as(client, "testuser")

        response = client.post("/student/plans/create", data={
            "subject": "数学",
            "semester": "八年级上册",
            "daily_goal": "not_a_number"
        })
        assert response.status_code != 500
