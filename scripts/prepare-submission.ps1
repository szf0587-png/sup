# Tianyan Cangqiong - Submission Package Builder
# Usage: .\scripts\prepare-submission.ps1 [-OutputZip "name.zip"] [-OutputDir "C:\path"]
param(
    [string]$OutputZip = "tianyan-cangqiong-submission.zip",
    [string]$OutputDir = ""
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$projectRoot = (Resolve-Path $projectRoot).Path

if (-not $OutputDir) {
    $OutputDir = Join-Path $projectRoot "..\submission"
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Package Builder" -ForegroundColor Cyan
Write-Host "========================================"

# --- Check required files ---
$required = @(
    "server\main.py", "server\config.py", "server\core_algorithms.py",
    "server\degradation.py", "server\api\standards.py", "server\api\phenology.py",
    "server\api\screening.py", "server\api\parcels.py", "server\api\reports.py",
    "server\services\phenology.py", "server\services\town_ranking.py",
    "server\services\parcel_evaluation.py", "server\services\spatial_analysis.py",
    "server\services\greenhouse_detection.py", "server\services\report_builder.py",
    "server\integrations\iserver_client.py", "server\integrations\udbx_publisher.py",
    "server\integrations\gee_client.py", "server\schemas\standards.py",
    "server\schemas\phenology.py", "server\schemas\screening.py",
    "scripts\start.ps1", "scripts\verify-coldstart.ps1", "requirements.txt",
    "frontend\index.html", "frontend\app.js", "frontend\styles.css",
    "frontend\golden_standard.html", "frontend\golden_standard.js",
    "frontend\map3d.html", "data\manifest.json", "data\golden_standards.json"
)

$missing = @()
foreach ($f in $required) {
    $path = Join-Path $projectRoot $f
    if (-not (Test-Path $path)) { $missing += $f }
}
if ($missing.Count -gt 0) {
    Write-Host "WARNING: Missing files:" -ForegroundColor Yellow
    $missing | ForEach-Object { Write-Host "  $_" }
} else {
    Write-Host "All required files present" -ForegroundColor Green
}

# --- Credential scan ---
Write-Host "[1/4] Scanning for credentials..."
$dangerous = Get-ChildItem $projectRoot -Recurse -Include "*.py","*.ps1","*.json" -ErrorAction SilentlyContinue |
    Select-String -Pattern "password\s*=\s*['`""][^$]" -List -ErrorAction SilentlyContinue |
    Where-Object { $_.Line -notmatch "ISERVER_PASSWORD|env\b|os\.getenv|Write-Warning|placeholder|your-" }

if ($dangerous) {
    Write-Host "  WARNING: possible credentials:" -ForegroundColor Red
    $dangerous | ForEach-Object { Write-Host "    $($_.Filename):$($_.LineNumber)" }
} else {
    Write-Host "  Clean - no credential leaks" -ForegroundColor Green
}

# --- Checksums ---
Write-Host "[2/4] Generating SHA256 checksums..."
$checksumFile = Join-Path $projectRoot "data\checksums.sha256"
Get-ChildItem $projectRoot -Recurse -File -Include "*.py","*.json","*.html","*.js","*.css","*.ps1","*.txt" -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch "\\.git\\|\\.omo\\|\\__pycache__\\|\.codegraph\\" } |
    ForEach-Object {
        $hash = (Get-FileHash -Path $_.FullName -Algorithm SHA256).Hash
        $relPath = $_.FullName.Replace($projectRoot + "\", "")
        "$hash  $relPath" | Out-File -FilePath $checksumFile -Append -Encoding UTF8
    }
Write-Host "  Written to data\checksums.sha256" -ForegroundColor Green

# --- Validate manifest ---
Write-Host "[3/4] Validating data manifest..."
$manifestPath = Join-Path $projectRoot "data\manifest.json"
if (Test-Path $manifestPath) {
    $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
    $missingData = ($manifest.datasets.PSObject.Properties | Where-Object { $_.Value.status -eq "missing" }).Count
    $fg = if ($missingData -eq 0) { "Green" } else { "Yellow" }
    Write-Host "  Manifest OK | $missingData datasets still need data" -ForegroundColor $fg
}

# --- Create ZIP ---
Write-Host "[4/4] Creating ZIP..."
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$zipPath = Join-Path $OutputDir $OutputZip
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }

$excludePatterns = @("\.git", "__pycache__", "\.codegraph", "\.omo", "node_modules", "\.gitignore", "main_tianyan\.py", "AHP_original\.py")
Push-Location $projectRoot
try {
    $files = Get-ChildItem . -Recurse -File |
        Where-Object {
            $rel = $_.FullName.Replace($projectRoot + "\", "")
            $exclude = $false
            foreach ($p in $excludePatterns) { if ($rel -match $p) { $exclude = $true; break } }
            -not $exclude
        }
    Compress-Archive -Path $files.FullName -DestinationPath $zipPath -Force
    $size = [math]::Round((Get-Item $zipPath).Length / 1MB, 2)
    Write-Host "  Created: $zipPath" -ForegroundColor Green
    Write-Host "  Size: $size MB"
}
finally { Pop-Location }

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Done: $zipPath" -ForegroundColor Cyan
Write-Host "========================================"
