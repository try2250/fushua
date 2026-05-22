# Claude Code 500 Investigation Report

Date: 2026-05-22
Project: `C:\Users\Windows 10\Desktop\trae\fushua`

## Executive Summary

Claude Code repeatedly failed in this project with gateway-side 500 responses.
The endpoint and account were usable, because a reduced safe launcher could
answer successfully. The failure was caused by automatic project context being
sent with each Claude Code request.

The decisive project-side trigger was an untracked diagnostic script name in
the Git working tree. The exact original phrase is intentionally not recorded in
this project file, because writing it back into project documents can recreate
the failure in IDE integrations that send open files or nearby documents as
context.

After removing that phrase from visible project context and simplifying the
assistant instruction files, normal Claude Code requests succeeded again.

## Impact

- A simple `test` prompt failed in this checkout.
- Claude Code retried repeatedly and never reached a usable assistant answer.
- Safe mode worked, which showed the API path was not fully broken.
- VSCode, Trae, and other integrations could fail again if they included the
  same local file names or documents in context.

## Environment

- Active checkout: `C:\Users\Windows 10\Desktop\trae\fushua`
- Claude Code version observed: `2.1.148`
- Gateway base URL: `https://52code.xin`
- Default model observed: `claude-opus-4-7`
- Installed user plugins:
  - `superpowers@claude-plugins-official`, version `5.1.0`
  - `andrej-karpathy-skills@karpathy-skills`, version `1.0.0`

## Investigation Approach

The debugging process changed one variable at a time:

1. Compare this project with an empty temporary directory.
2. Compare normal mode with safe mode.
3. Disable plugins temporarily.
4. Temporarily move user-level skills out of the load path.
5. Temporarily remove project instruction files.
6. Temporarily rename the diagnostic script.
7. Re-run normal Claude Code after each change.

All temporary moves were restored during probing unless the final fix required a
permanent cleanup.

## Evidence Matrix

| Probe | Result | Meaning |
| --- | --- | --- |
| Safe launcher in this project | Passed | Credentials and gateway route were usable. |
| Normal Claude in empty temp directory | Passed | Global install was not completely broken. |
| Normal Claude in this project | Failed | Project context was involved. |
| Temporarily disable installed plugins | Failed | Plugins alone were not the root cause. |
| Temporarily disable plugin hook context | Failed | Hook context was only an amplifier. |
| Disable tools only | Failed | Tool definitions were not the root cause. |
| Bare mode only | Failed | Bare mode alone did not remove every triggering input. |
| Bare mode plus short prompt | Passed | Short context path avoided the issue. |
| Empty directory with reduced skill/plugin load | Passed | Baseline environment was healthy. |
| This project with reduced skill/plugin load | Failed | Project metadata remained the difference. |
| Temporarily remove `CLAUDE.md` | Passed under reduced conditions | Project instructions contributed context. |
| Temporarily remove `AGENTS.md` | Still failed | `AGENTS.md` was not the sole trigger. |
| Temporarily rename the diagnostic script | Passed path reached | Git status filename was the decisive trigger. |
| Final normal Claude run after cleanup | Passed | Practical issue was resolved. |

## Root Cause

Claude Code includes more than the visible user message. It can include project
metadata such as:

- Current working directory
- Git state
- Project instruction files
- Skill/plugin descriptions
- Hook-provided context

In this incident, Git state exposed an untracked diagnostic filename containing
a phrase that the gateway rejected. That filename appeared in the request even
when the user prompt was only `test`.

The installed plugin set made the request larger, but it was not sufficient to
cause failure by itself. After cleanup, the same plugin set loaded and normal
Claude Code succeeded.

## Fixes Applied

### 1. Removed the triggering filename from project context

The old diagnostic script filename was changed. The project should not restore
that exact original filename.

### 2. Simplified `CLAUDE.md`

The file now only keeps:

- Active project path
- PowerShell guidance
- UTF-8 guidance
- Narrow verification commands
- Minimal local caveats

Removed:

- Stale checkout paths
- WSL path examples
- Direct discussion of the prior trigger

### 3. Simplified `AGENTS.md`

The Codex instruction file was aligned with `CLAUDE.md`, so other assistants do
not bring the old context back.

### 4. Preserved safe launcher

The safe launcher remains a fallback for checking whether the account and
gateway route are alive.

## Additional Hardening After Recurrence

After the issue triggered again, the project documentation was rewritten to
avoid recording the rejected phrase or a large amount of gateway-rule language
inside the checkout.

The temporary diagnostic script should not remain in the project root. If it is
needed later, keep it outside this checkout or rename it with neutral wording and
avoid opening it in the same IDE session used for Claude.

Generated Claude worktrees should also stay outside the active checkout. They
contain full copied project trees and old notes, which increases the chance that
IDE integrations send irrelevant context.

## Verification Commands

Normal Claude Code smoke test:

```powershell
claude -p "test" --output-format json --max-budget-usd 0.08
```

Safe launcher smoke test:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-claude-safe-chat.ps1 -Once "test" -MaxBudgetUsd 0.03
```

Project checks:

```powershell
python -m compileall -q app tests
python -m pytest tests/test_backup.py -q --tb=short
python -c "from app.main import app; print('import ok')"
```

## Verification Results From First Fix

The first successful normal Claude run returned:

```text
subtype: success
result: I'm here and ready to help. What would you like to work on?
```

The debug log still showed plugin and skill loading, then reached streaming:

```text
Registered 1 hooks from 2 plugins
Total plugin skills loaded: 15
getSkills returning: 15 skill dir commands, 15 plugin skills, 13 bundled skills
Stream started - received first chunk
```

Project checks also passed:

```text
compileall ok
5 passed, 10 warnings
```

## Prevention Checklist

Before opening Claude in this checkout:

1. Run `git status --short`.
2. Look for new untracked diagnostic files with security-gateway wording.
3. Keep `CLAUDE.md` and `AGENTS.md` short.
4. Keep detailed incident notes free of rejected phrases.
5. Keep generated worktrees outside the active checkout.
6. Restart the IDE extension host after cleanup so stale context is not reused.

## If It Happens Again

Use this order:

1. Run the safe launcher. If it fails too, check account, model, and gateway.
2. Run normal `claude -p "test"` from an empty temp directory.
3. Run `git status --short` in this project.
4. Temporarily move newly added docs or diagnostic files out of the checkout.
5. Temporarily disable plugins only after project context has been checked.
6. Re-test normal Claude from the project root.

## Conclusion

The practical root cause was project context, not the visible prompt. The most
important prevention is to keep rejected gateway-rule language and diagnostic
payload names out of files that Claude or an IDE may include automatically.
