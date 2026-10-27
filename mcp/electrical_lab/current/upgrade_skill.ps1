$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Source = Join-Path $Root 'skills\electrical-training'
$Target = Join-Path $HOME '.codex\skills\electrical-training'
if (Test-Path $Target) {
  $Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
  $Backup = "${Target}_backup_$Stamp"
  Move-Item -Path $Target -Destination $Backup
  Write-Host "旧版 Skill 已备份至：$Backup" -ForegroundColor Yellow
}
New-Item -ItemType Directory -Force (Split-Path $Target) | Out-Null
Copy-Item -Path $Source -Destination $Target -Recurse
Write-Host "已安装 / 升级至：$Target" -ForegroundColor Green
Write-Host "MCP 配置仍需参照 README.md 设置路径并重启 Codex。" -ForegroundColor Cyan

# v3 新增工业素材 Skill（不覆盖已有 Skill）
$SourceAssets = Join-Path $Root 'skills\industrial-assets'
$TargetAssets = Join-Path $HOME '.codex\skills\industrial-assets'
if (Test-Path $TargetAssets) {
    $StampAssets = Get-Date -Format 'yyyyMMdd_HHmmss'
    $BackupAssets = "${TargetAssets}_backup_$StampAssets"
    Move-Item -Path $TargetAssets -Destination $BackupAssets
    Write-Host "旧版 industrial-assets Skill 已备份至：$BackupAssets" -ForegroundColor Yellow
}
if (!(Test-Path $TargetAssets)) {
    New-Item -ItemType Directory -Force (Split-Path $TargetAssets) | Out-Null
    Copy-Item -Path $SourceAssets -Destination $TargetAssets -Recurse
    Write-Host "安装 industrial-assets Skill: $TargetAssets" -ForegroundColor Green
}
