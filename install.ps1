param(
  [string]$Target = "."
)
$ErrorActionPreference = "Stop"
$src = Split-Path -Parent $MyInvocation.MyCommand.Path
New-Item -ItemType Directory -Force -Path (Join-Path $Target "scripts") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Target "skills/orchestrator") | Out-Null
Copy-Item (Join-Path $src "scripts/roach.py") (Join-Path $Target "scripts/roach.py") -Force
Copy-Item (Join-Path $src "scripts/providers.py") (Join-Path $Target "scripts/providers.py") -Force
Copy-Item (Join-Path $src "skills/orchestrator/SKILL.md") (Join-Path $Target "skills/orchestrator/SKILL.md") -Force
Write-Host "Roach Loop installed in $Target"
Write-Host 'Next: python scripts/roach.py init --name "My Product"'
