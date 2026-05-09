import os
import yaml
import pytest


def test_ci_yml_exists():
    ci_path = os.path.join(os.path.dirname(__file__), '..', '.github', 'workflows', 'ci.yml')
    assert os.path.exists(ci_path), f"CI config file not found at {ci_path}"


def test_ci_yml_valid_yaml():
    ci_path = os.path.join(os.path.dirname(__file__), '..', '.github', 'workflows', 'ci.yml')
    with open(ci_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    assert config is not None, "CI config should not be empty"


def test_ci_yml_contains_pytest():
    ci_path = os.path.join(os.path.dirname(__file__), '..', '.github', 'workflows', 'ci.yml')
    with open(ci_path, 'r', encoding='utf-8') as f:
        content = f.read()
    assert 'pytest' in content, "CI config should contain pytest command"


def test_ci_yml_contains_alembic():
    ci_path = os.path.join(os.path.dirname(__file__), '..', '.github', 'workflows', 'ci.yml')
    with open(ci_path, 'r', encoding='utf-8') as f:
        content = f.read()
    assert 'alembic upgrade head' in content, "CI config should contain alembic upgrade head command"
