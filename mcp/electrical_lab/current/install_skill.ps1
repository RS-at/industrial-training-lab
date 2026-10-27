$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Source = Join-Path $Root 'skills\electrical-training'
$Target = Join-Path $HOME '.codex\skills\electrical-training'
if (Test-Path $Target) {
    Write-Host "目录已存在；未覆盖：$Target" -ForegroundColor Yellow
    Write-Host "请先自行备份旧 Skill 后再安装。"
    exit 1
}
New-Item -ItemType Directory -Force (Split-Path $Target) | Out-Null
Copy-Item -Path $Source -Destination $Target -Recurse
Write-Host "Skill 已复制至: $Target" -ForegroundColor Green
Write-Host "MCP 需按 README.md 配置绝对路径；安装程序不会改动你的 Codex 配置。"

# v3 新增工业素材 Skill（不覆盖已有 Skill）
$SourceAssets = Join-Path $Root 'skills\industrial-assets'
$TargetAssets = Join-Path $HOME '.codex\skills\industrial-assets'
if (!(Test-Path $TargetAssets)) {
    New-Item -ItemType Directory -Force (Split-Path $TargetAssets) | Out-Null
    Copy-Item -Path $SourceAssets -Destination $TargetAssets -Recurse
    Write-Host "安装 industrial-assets Skill: $TargetAssets" -ForegroundColor Green
} else { Write-Host "industrial-assets 已存在，未覆盖。请手动升级。" -ForegroundColor Yellow }
