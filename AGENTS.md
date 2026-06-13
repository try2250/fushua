# Fushua Codex Instructions

## Project Root

Always work from this directory:

```powershell
C:\Users\Windows 10\Desktop\trae\fushua
```

The active FastAPI checkout is `fushua`. Ignore older checkout locations that
may appear in previous logs or notes.

## Shell And Encoding

Use PowerShell-style commands on Windows. Avoid WSL-only commands and Unix-only
helpers.

For Python commands that print non-ASCII text, set UTF-8 output:

```powershell
$env:PYTHONIOENCODING='utf-8'
```

## Verification Commands

Use narrow checks first:

```powershell
python -m compileall -q app tests
python -m pytest tests/test_backup.py -q --tb=short
python -c "from app.main import app; print('import ok')"
```

For the full suite, allow at least 5 minutes:

```powershell
$env:PYTHONIOENCODING='utf-8'; python -m pytest tests/ -q --tb=short --disable-warnings --maxfail=1
```

The full suite can take more than 3 minutes on this machine. Do not treat a
short timeout as a test failure.

## Code Review

本项目有完整的代码审查标准。审查前请阅读：

- **审查标准**: `docs/code-review-standards.md`
- **速查卡**: `docs/code-review-cheatsheet.md`
- **PR 模板**: `.github/pull_request_template.md`

### 自动化工具

```powershell
# 安装开发工具
pip install -r dev-requirements.txt
pre-commit install

# 手动 lint
ruff check app/ tests/
ruff format app/ tests/

# 运行测试
python -m pytest tests/ -v --tb=short
```

## Current Local Caveats

- `test_logging.py` imports `requests`, but the project dependency list uses
  `httpx`; prefer project tests under `tests/` unless this script is updated.
- Check `git status --short` before edits. This workspace may already contain
  unrelated local changes.
