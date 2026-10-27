# Install one project-scoped Codex Blender MCP and one corresponding Skill.
# Backs up before editing; disables legacy Blender/DSH MCP entries in trusted workspace.
param([Parameter(Mandatory=$true)][string]$Workspace)
$ErrorActionPreference='Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Workspace = [IO.Path]::GetFullPath($Workspace)
if (!(Test-Path -LiteralPath $Workspace -PathType Container)) { throw "Workspace directory not found: $Workspace" }
# Fetch pinned, complete upstream engine first. Abort before mutating Codex config on network errors.
& (Join-Path $Root 'BOOTSTRAP_DSH.ps1')
if (!(Get-Command uv -ErrorAction SilentlyContinue)) {throw 'Install uv first: https://docs.astral.sh/uv/' }
& uv sync --directory $Root --no-dev
if ($LASTEXITCODE -ne 0) { throw 'uv sync failed' }
$python = Join-Path $Root '.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $python)) {throw 'Cannot find venv Python executable'}
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$backupDir = Join-Path $Workspace ('.blender_v3_backups\'+$stamp)
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
$skillSource = Join-Path $Root 'skills\industrial-blender-v3'
$skillTarget = Join-Path $Workspace '.agents\skills\industrial-blender-v3'
if (Test-Path -LiteralPath $skillTarget) {
    Copy-Item -LiteralPath $skillTarget -Destination (Join-Path $backupDir 'industrial-blender-v3_old_skill') -Recurse
    Remove-Item -LiteralPath $skillTarget -Recurse -Force
}
New-Item -ItemType Directory -Path (Split-Path $skillTarget) -Force | Out-Null
Copy-Item -LiteralPath $skillSource -Destination $skillTarget -Recurse
$modelingSource = Join-Path $Root 'skills\blender-modeling'
$modelingTarget = Join-Path $Workspace '.agents\skills\blender-modeling'
if (Test-Path -LiteralPath $modelingTarget) {
    $resolvedModeling = [IO.Path]::GetFullPath($modelingTarget)
    if (!$resolvedModeling.StartsWith($Workspace + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Skill target outside workspace' }
    Move-Item -LiteralPath $modelingTarget -Destination (Join-Path $backupDir 'blender-modeling_old_skill')
}
Copy-Item -LiteralPath $modelingSource -Destination $modelingTarget -Recurse

$configDir = Join-Path $Workspace '.codex'
New-Item -ItemType Directory -Path $configDir -Force | Out-Null
$configPath = Join-Path $configDir 'config.toml'
$raw = ''
if (Test-Path -LiteralPath $configPath) {
    $raw = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8
    Copy-Item -LiteralPath $configPath -Destination (Join-Path $backupDir 'codex_config_original.toml')
}
# Merge project + global server names, disable only Blender/DSH matches, not unrelated MCPs.
$globalPath = Join-Path $HOME '.codex\config.toml'
$globalNames = @()
if (Test-Path -LiteralPath $globalPath) {
    $g = Get-Content -LiteralPath $globalPath -Raw -Encoding UTF8
    $globalNames = @([regex]::Matches($g,'(?m)^\[mcp_servers\.([^\]]+)\]') | ForEach-Object { $_.Groups[1].Value })
}
$lines = @($raw -split '\r?\n')
$newLines = New-Object 'System.Collections.Generic.List[string]'
$legacyName = $null
$legacyHasEnabled = $false
$skipCurrent = $false
$existingNames = @()
foreach ($line in $lines) {
    if ($line -match '^\s*\[([^\]]+)\]\s*$') {
        if ($null -ne $legacyName -and -not $legacyHasEnabled) { $newLines.Add('enabled = false') }
        $legacyName=$null; $legacyHasEnabled=$false; $skipCurrent=$false
        $table=$Matches[1]
        if ($table -match '^mcp_servers\.(.+)$') {
            $name=$Matches[1];$existingNames+= $name
            if ($name -eq 'industrial_blender') {$skipCurrent=$true;continue}
            if ($name -match '(?i)blender|dsh') {$legacyName=$name}
        }
    }
    if ($skipCurrent) {continue}
    if ($null -ne $legacyName -and $line -match '^\s*enabled\s*=') {
        $newLines.Add('enabled = false');$legacyHasEnabled=$true;continue
    }
    $newLines.Add($line)
}
if ($null -ne $legacyName -and -not $legacyHasEnabled) { $newLines.Add('enabled = false') }
# Project-level entries override global entries with the same name for trusted projects.
foreach ($name in $globalNames) {
    if ($name -ne 'industrial_blender' -and $name -match '(?i)blender|dsh' -and $name -notin $existingNames) {
        $newLines.Add('');$newLines.Add("[mcp_servers.$name]");$newLines.Add('enabled = false')
    }
}
$py = $python.Replace('\','/')
$server = (Join-Path $Root 'server\main.py').Replace('\','/')
$newLines.Add('')
$newLines.Add('[mcp_servers.industrial_blender]')
$newLines.Add("command = `"$py`"")
$newLines.Add("args = [`"$server`"]")
$newLines.Add('enabled = true')
[IO.File]::WriteAllText($configPath,($newLines -join "`n")+"`n",[Text.UTF8Encoding]::new($false))
Write-Host 'Installed ONE industrial_blender MCP for this trusted workspace.' -ForegroundColor Green
Write-Host "Config: $configPath"
Write-Host "Skill: $skillTarget"
Write-Host "Backup: $backupDir"
Write-Host 'Blender/DSH legacy MCP entries were disabled at project scope (unrelated MCPs unchanged).'
Write-Host 'Start backend in a separate terminal: .\START_DSH_BACKEND.ps1'
Write-Host 'Enable upstream addon/dsh_blender_bridge.py in Blender GUI, then call blender_dsh_status and check doctor.kind=ok.'
Write-Host 'Open your trusted project in local Codex, restart session, call blender_status.'
