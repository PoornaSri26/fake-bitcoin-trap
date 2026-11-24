#!/usr/bin/env pwsh
# PowerShell stand-in for `make reproduce`.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$env:PYTHONPATH = "src"
$py = if ($env:PY) { $env:PY } else { "python" }
$stages = if ($args.Count -gt 0) { $args } else { @("nulls","trials","neff","dsr","charts") }
foreach ($s in $stages) {
    Write-Host "== stage: $s"
    & $py -m btrap.pipeline $s
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
Write-Host "reproduced without touching the holdout."
