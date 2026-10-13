# run_kofty.ps1 — invoke the globally-installed kofty from the project root.
# No venv needed: kofty.exe lives at
#   C:\Users\elrad\AppData\Local\Programs\Python\Python313\Scripts\kofty.exe
# and is on the user PATH.

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$ErrorActionPreference = "Stop"

# Always run from the project root so build\ lands in the right place,
# regardless of where VS Code launched the task from.
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$koftyCmd = Get-Command kofty -ErrorAction SilentlyContinue
if (-not $koftyCmd) {
    Write-Host "[run_kofty] 'kofty' not found on PATH." -ForegroundColor Red
    Write-Host "            Expected: $env:LOCALAPPDATA\Programs\Python\Python313\Scripts\kofty.exe" -ForegroundColor Red
    Write-Host "            Fix: run 'pip install -e .' from $root" -ForegroundColor Red
    exit 127
}

& kofty @Args
exit $LASTEXITCODE

