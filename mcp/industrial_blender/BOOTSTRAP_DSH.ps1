# Retrieve exact, unmodified BSD-3-Clause DSH engine under vendor/.
param([switch]$ForceRefresh)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Repo = Join-Path $Root 'vendor\dsh-blender-plugin'
$Lock = Get-Content (Join-Path $Root 'bridge\upstream.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if (!(Get-Command git -ErrorAction SilentlyContinue)) { throw 'Git for Windows is required: https://git-scm.com/download/win' }
if (!(Get-Command node -ErrorAction SilentlyContinue)) { throw 'Node.js >=20 is required: https://nodejs.org/' }
$NodeMajor = [int]((& node -p 'process.versions.node').Split('.')[0])
if ($NodeMajor -lt 20) { throw 'Node.js >=20 is required' }
if ((Test-Path $Repo) -and -not (Test-Path (Join-Path $Repo '.git'))) { throw "vendor path exists but is not a Git checkout: $Repo" }
 $Fresh = !(Test-Path $Repo)
if ($Fresh) {
    & git clone --filter=blob:none --no-checkout $Lock.repository $Repo
    if ($LASTEXITCODE -ne 0) { throw 'Clone failed; configure git network/proxy and retry' }
}
$Old = (Get-Location).Path
try {
    Set-Location $Repo
    & git fetch --depth 1 origin $Lock.commit
    if ($LASTEXITCODE -ne 0) { throw 'Fetch pinned commit failed' }
    if ($ForceRefresh) { Write-Warning 'ForceRefresh requested. Do not overwrite uncommitted upstream edits.' }
    # A fresh --no-checkout tree marks every tracked file as absent. That is expected.
    if (-not $Fresh) {
        $status = (& git status --porcelain)
        if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect checkout status' }
        if ($status) { throw 'Upstream checkout contains local changes; refusing checkout' }
    }
    & git checkout --detach $Lock.commit
    if ($LASTEXITCODE -ne 0) { throw 'Checkout failed' }
    $Actual = (& git rev-parse HEAD).Trim()
    if ($Actual -ne $Lock.commit) { throw "Commit mismatch: $Actual" }
    foreach ($file in @('runtime\server.mjs','runtime\engine.mjs','runtime\catalog.mjs','addon\dsh_blender_bridge.py','LICENSE')) {
        if (!(Test-Path $file)) { throw "Required upstream file missing: $file" }
    }
    Write-Host "Pinned DSH source OK: $Actual" -ForegroundColor Green
    Write-Host "Blender add-on path: $(Join-Path $Repo 'addon\dsh_blender_bridge.py')"
    Write-Host 'Source license: BSD-3-Clause. Preserve LICENSE and upstream copyright.'
} finally { Set-Location $Old }
