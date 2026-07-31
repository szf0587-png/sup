# 天眼寻珍·苍穹 — 冷启动验证脚本
# 用法: .\scripts\verify-coldstart.ps1 -Iterations 3 -OfflineTest
param(
    [int]$Iterations = 3,
    [switch]$OfflineTest,
    [int]$StartupWait = 30
)

$ErrorActionPreference = "Stop"
$workspace = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Join-Path $workspace ".."
$serverDir = Join-Path $projectRoot "server"

$python = "D:\Conda_Data\envs\terroir_hunter\python.exe"
$iserverDir = "E:\supermap-iserver-2026-windows-x64-deploy"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " 天眼寻珍·苍穹 — 冷启动验证" -ForegroundColor Cyan
Write-Host " 迭代次数: $Iterations | 断网测试: $OfflineTest" -ForegroundColor Cyan
Write-Host "========================================"

# --- 预检查 ---
if (-not (Test-Path $python)) { Write-Error "Python not found: $python"; exit 1 }
if (-not (Test-Path $iserverDir)) { Write-Error "iServer not found: $iserverDir"; exit 1 }

$results = @()

for ($i = 1; $i -le $Iterations; $i++) {
    $roundLabel = if ($OfflineTest -and $i -eq $Iterations) { "OFFLINE #$i" } else { "Round #$i" }
    Write-Host "`n--- $roundLabel ---" -ForegroundColor Yellow

    # 1. 停止所有服务
    Write-Host "  Stopping services..."
    Get-Process -Name "python*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Get-Process -Name "java*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 5

    # 2. 清空临时输出
    $snapshotsDir = Join-Path $projectRoot "data\snapshots"
    if (Test-Path $snapshotsDir) {
        Get-ChildItem $snapshotsDir -Filter "*.json" -ErrorAction SilentlyContinue | ForEach-Object {
            if ($_.Name -notlike "facilities_*") { Remove-Item $_.FullName -Force }
        }
    }

    # 3. 断网测试模式
    if ($OfflineTest -and $i -eq $Iterations) {
        Write-Host "  !! OFFLINE MODE - Disable network adapter if possible" -ForegroundColor Red
        $env:GEE_OFFLINE = "1"
        $env:AI_OFFLINE = "1"
        $env:NO_PROXY = "*"
    }

    # 4. 启动 iServer
    Write-Host "  Starting iServer..."
    $env:PATH = "E:\SuperMap\bin;$env:PATH"
    Start-Process -FilePath "$iserverDir\bin\startup.bat" -WorkingDirectory "$iserverDir\bin" -WindowStyle Minimized

    # 5. 等待 iServer
    Write-Host "  Waiting for iServer ($StartupWait s)..."
    $iserverReady = $false
    for ($w = 0; $w -lt $StartupWait; $w += 3) {
        Start-Sleep -Seconds 3
        try {
            $r = Invoke-WebRequest -Uri "http://127.0.0.1:8090/iserver/services" -UseBasicParsing -TimeoutSec 3
            if ($r.StatusCode -eq 200) { $iserverReady = $true; break }
        } catch {}
    }

    if (-not $iserverReady) {
        Write-Host "  FAIL: iServer not ready after ${StartupWait}s" -ForegroundColor Red
        $results += @{ round = $roundLabel; iserver = "FAIL"; fastapi = "SKIP"; report = "SKIP" }
        continue
    }
    Write-Host "  iServer: OK" -ForegroundColor Green

    # 6. 启动 FastAPI
    Write-Host "  Starting FastAPI..."
    $fastapiProcess = Start-Process -FilePath $python -ArgumentList $serverDir\main.py -PassThru -NoNewWindow
    Start-Sleep -Seconds 5

    # 7. 验证 FastAPI
    $fastapiReady = $false
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/system/status" -UseBasicParsing -TimeoutSec 5
        if ($r.StatusCode -eq 200) {
            $status = $r.Content | ConvertFrom-Json
            Write-Host "  FastAPI: OK (iServer: $($status.services.iserver))" -ForegroundColor Green
            $fastapiReady = $true
        }
    } catch {
        Write-Host "  FastAPI check failed: $_" -ForegroundColor Red
    }

    # 8. 验证核心 API
    $apiOk = $false
    if ($fastapiReady) {
        try {
            $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/golden-standards/list" -UseBasicParsing -TimeoutSec 5
            $apiOk = ($r.StatusCode -eq 200)
            Write-Host "  API check: $(if ($apiOk) { 'OK' } else { 'FAIL' })" -ForegroundColor $(if ($apiOk) { 'Green' } else { 'Red' })
        } catch {
            Write-Host "  API check: FAIL ($_)" -ForegroundColor Red
        }
    }

    $results += @{
        round = $roundLabel
        iserver = if ($iserverReady) { "OK" } else { "FAIL" }
        fastapi = if ($fastapiReady) { "OK" } else { "FAIL" }
        api = if ($apiOk) { "OK" } else { "FAIL" }
    }
}

# --- 汇总 ---
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " 验证结果汇总" -ForegroundColor Cyan
Write-Host "========================================"

$pass = 0
$fail = 0
foreach ($r in $results) {
    $allOk = ($r.iserver -eq "OK" -and $r.fastapi -eq "OK" -and $r.api -eq "OK")
    $status = if ($allOk) { "PASS" } else { "FAIL" }
    if ($allOk) { $pass++ } else { $fail++ }
    Write-Host "  $($r.round): $status (iServer=$($r.iserver) FastAPI=$($r.fastapi) API=$($r.api))" -ForegroundColor $(if ($allOk) { 'Green' } else { 'Red' })
}

Write-Host "`nTotal: $pass PASS, $fail FAIL" -ForegroundColor $(if ($fail -eq 0) { 'Green' } else { 'Red' })

if ($fail -gt 0) { exit 1 } else { exit 0 }
