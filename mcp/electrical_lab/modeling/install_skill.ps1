$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Parent = Join-Path $HOME '.codex\skills'
$SkillNames = @('electrical-training','industrial-asset-modeling')
New-Item -ItemType Directory -Force $Parent | Out-Null
foreach ($Name in $SkillNames) {
    $Source = Join-Path $Root (Join-Path 'skills' $Name)
    $Target = Join-Path $Parent $Name
    if (Test-Path $Target) {
        Write-Host "Skill 已存在，未覆盖：$Target" -ForegroundColor Yellow
        Write-Host "若需升级，请运行 upgrade_skill.ps1（自动备份旧版）。"
        continue
    }
    Copy-Item -Path $Source -Destination $Target -Recurse
    Write-Host "Skill 已安装：$Target" -ForegroundColor Green
}
Write-Host 'MCP 需按 README.md 手动添加 Codex config.toml 路径。'
