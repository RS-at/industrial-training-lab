$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Parent = Join-Path $HOME '.codex\skills'
$SkillNames = @('electrical-training','industrial-asset-modeling')
New-Item -ItemType Directory -Force $Parent | Out-Null
foreach ($Name in $SkillNames) {
    $Source = Join-Path $Root (Join-Path 'skills' $Name)
    $Target = Join-Path $Parent $Name
    if (Test-Path $Target) {
       $Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
       $Backup = "${Target}_backup_$Stamp"
       Move-Item -Path $Target -Destination $Backup
       Write-Host "旧 Skill 已备份：$Backup" -ForegroundColor Yellow
    }
    Copy-Item -Path $Source -Destination $Target -Recurse
    Write-Host "Skill 已安装/升级：$Target" -ForegroundColor Green
}
Write-Host '更新 MCP 时请把 config.toml 中的脚本路径指向当前 v3 文件夹，并重启 Codex。'
