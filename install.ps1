param(
  [string]$Target = "."
)
$ErrorActionPreference = "Stop"
$src = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Test-Path (Join-Path $Target ".git"))) {
  throw "Roach Loop requires the target to be a Git repository: $Target"
}

foreach ($dir in @("scripts","skills","schemas","hooks","templates")) {
  New-Item -ItemType Directory -Force -Path (Join-Path $Target $dir) | Out-Null
}

Copy-Item (Join-Path $src "scripts/roach.py") (Join-Path $Target "scripts/roach.py") -Force
Copy-Item (Join-Path $src "scripts/providers.py") (Join-Path $Target "scripts/providers.py") -Force
Copy-Item (Join-Path $src "skills/*") (Join-Path $Target "skills") -Recurse -Force
Copy-Item (Join-Path $src "schemas/*") (Join-Path $Target "schemas") -Recurse -Force
Copy-Item (Join-Path $src "hooks/*") (Join-Path $Target "hooks") -Recurse -Force
Copy-Item (Join-Path $src "templates/*") (Join-Path $Target "templates") -Recurse -Force

@"
# Roach Loop agent contract

This repository uses Roach Loop.
Before substantial work run: python scripts/roach.py next
For an active checkpoint run: python scripts/roach.py context <checkpoint> --role worker --json
Never manually edit Roach-managed gate state or fabricate evidence.
Before claiming completion run: python scripts/roach.py verify-project
Stop when Roach requires human judgment.
"@ | Set-Content (Join-Path $Target "ROACH-AGENT.md")

Write-Host "Roach Loop installed in $Target"
Write-Host 'Next: python scripts/roach.py init --name "My Product" --profile standard'
