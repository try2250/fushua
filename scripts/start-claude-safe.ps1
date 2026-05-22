$ErrorActionPreference = "Stop"
$ClaudeArgs = $args

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

if ($ClaudeArgs.Count -eq 0 -and ([Console]::IsInputRedirected -or [Console]::IsOutputRedirected)) {
    Write-Error "Interactive Claude requires a real terminal window. Double-click the safe-mode BAT file or open it from Windows Terminal."
    exit 1
}

$systemPrompt = @"
You are Claude Code working in this repository:
C:\Users\Windows 10\Desktop\trae\fushua

Project rules:
- Use PowerShell-style commands on Windows.
- Stay in the fushua checkout; do not use old non-ASCII path variants, WSL paths, /mnt/c paths, or /c/Users paths.
- Prefer narrow verification before broad test runs.
- For full tests, allow several minutes. Use UTF-8 output when command output includes non-ASCII text.
- Check git status before edits. Do not revert unrelated local changes.
"@

$claudeCommandArgs = @("--bare", "--model", "claude-sonnet-4-6", "--system-prompt", $systemPrompt) + $ClaudeArgs

if ($env:FUSHUA_CLAUDE_DEBUG_ARGS -eq "1") {
    $claudeCommandArgs | ForEach-Object { Write-Output "ARG=[$_]" }
    exit 0
}

if ($ClaudeArgs.Count -eq 0) {
    Write-Host "Starting Claude safe mode in $ProjectRoot"
    Write-Host "Mode: --bare, model: claude-sonnet-4-6"
    Write-Host "Reason: avoids the proxy filter triggered by default Claude Code context and superpowers startup hooks."
    Write-Host ""
}

& claude @claudeCommandArgs
exit $LASTEXITCODE
