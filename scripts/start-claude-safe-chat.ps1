param(
    [string]$Once,
    [decimal]$MaxBudgetUsd = 0.08,
    [int]$MaxHistoryChars = 12000,
    [switch]$EnableTools
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new()

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

$systemPrompt = @"
You are a concise assistant working in this repository:
C:\Users\Windows 10\Desktop\trae\fushua

Project rules:
- Use PowerShell-style commands on Windows.
- Stay in the fushua checkout.
- Do not use old path variants, WSL paths, /mnt/c paths, or /c/Users paths.
- Keep normal chat replies short unless the user asks for detail.
- If the user sends only "test" or "测试", reply exactly "OK".
- Do not claim to inspect files or run commands unless tools are enabled.
"@

function Invoke-ClaudeTurn {
    param(
        [string]$PromptText
    )

    $budget = $MaxBudgetUsd.ToString("0.00", [Globalization.CultureInfo]::InvariantCulture)
    $claudeArgs = @(
        "--bare",
        "--model", "claude-sonnet-4-6",
        "--system-prompt", $systemPrompt,
        "--output-format", "json",
        "--max-budget-usd", $budget,
        "-p", $PromptText
    )

    if (-not $EnableTools) {
        $claudeArgs = @("--tools", "") + $claudeArgs
    }

    $raw = & claude @claudeArgs
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        Write-Host ""
        Write-Host "[Claude exited with code $exitCode]" -ForegroundColor Red
        $raw | ForEach-Object { Write-Host $_ }
        return $null
    }

    try {
        return ($raw | Out-String | ConvertFrom-Json)
    } catch {
        Write-Host ""
        Write-Host "[Could not parse Claude output]" -ForegroundColor Red
        $raw | ForEach-Object { Write-Host $_ }
        return $null
    }
}

function New-PromptWithHistory {
    param(
        [string]$UserText,
        [System.Collections.Generic.List[string]]$History
    )

    if ($History.Count -eq 0) {
        return $UserText
    }

    $joined = ($History -join "`n`n")
    if ($joined.Length -gt $MaxHistoryChars) {
        $joined = $joined.Substring($joined.Length - $MaxHistoryChars)
    }

    return @"
Conversation so far:
$joined

Current user message:
$UserText
"@
}

if ($Once) {
    $result = Invoke-ClaudeTurn -PromptText $Once
    if ($null -ne $result) {
        Write-Output $result.result
    }
    exit $LASTEXITCODE
}

Write-Host "Claude safe chat for fushua"
Write-Host "Mode: print-mode loop, model: claude-sonnet-4-6"
if ($EnableTools) {
    Write-Host "Tools: enabled"
} else {
    Write-Host "Tools: disabled for stable chat"
}
Write-Host "Commands: /exit, /clear"
Write-Host ""

$history = [System.Collections.Generic.List[string]]::new()

while ($true) {
    $userText = Read-Host "you"
    if ([string]::IsNullOrWhiteSpace($userText)) {
        continue
    }

    if ($userText -eq "/exit") {
        break
    }

    if ($userText -eq "/clear") {
        $history.Clear()
        Write-Host "[history cleared]"
        continue
    }

    $promptText = New-PromptWithHistory -UserText $userText -History $history
    $result = Invoke-ClaudeTurn -PromptText $promptText
    if ($null -eq $result) {
        continue
    }

    Write-Host ""
    Write-Host "claude>" -ForegroundColor Cyan
    Write-Host $result.result
    Write-Host ""

    $history.Add("User: $userText")
    $history.Add("Assistant: $($result.result)")
}
