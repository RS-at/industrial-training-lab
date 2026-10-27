# Start the non-MCP DSH HTTP execution backend (loopback only, port 9877).
param([switch]$NoStartIfRunning)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Server = Join-Path $Root 'vendor\dsh-blender-plugin\runtime\server.mjs'
if (!(Test-Path $Server)) { throw 'Missing upstream source: run BOOTSTRAP_DSH.ps1' }
if (!(Get-Command node -ErrorAction SilentlyContinue)) { throw 'Install Node.js >= 20' }
try {
    $h=Invoke-RestMethod 'http://127.0.0.1:9877/health' -TimeoutSec 2
    if ($h) { Write-Host 'Backend already listening. Confirm provenance and doctor before using.'; exit 0 }
} catch { }
Write-Host 'Starting upstream HTTP engine on loopback port 9877 (this is NOT a second MCP server).'
Write-Host 'Keep this terminal open. Start Blender separately and enable DSH Blender Bridge on 127.0.0.1:9876.'
& node $Server --port 9877
