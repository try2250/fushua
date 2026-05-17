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


def test_ci_test_step_sets_environment_inside_env():
    ci_path = os.path.join(os.path.dirname(__file__), '..', '.github', 'workflows', 'ci.yml')
    with open(ci_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    steps = config['jobs']['test']['steps']
    test_step = next(step for step in steps if step.get('name') == 'Run tests')

    assert test_step['env']['DATABASE_URL'] == 'sqlite:///./test_ci.db'
    assert test_step['env']['ENVIRONMENT'] == 'test'
    assert 'ENVIRONMENT' not in test_step
