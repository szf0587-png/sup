param(
    [string]$GcpProjectId,
    [string]$ProxyUrl = "",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

# --- 环境变量 ---
if ($GcpProjectId) {
    $env:GCP_PROJECT_ID = $GcpProjectId
    $env:GOOGLE_CLOUD_PROJECT = $GcpProjectId
}
if ($ProxyUrl) {
    $env:HTTP_PROXY = $ProxyUrl
    $env:HTTPS_PROXY = $ProxyUrl
}

$env:FASTAPI_HOST = "127.0.0.1"
$env:FASTAPI_PORT = "$Port"

# ISERVER_PASSWORD is provided by the caller and never stored in source.
if (-not $env:ISERVER_PASSWORD) {
    Write-Warning "ISERVER_PASSWORD not set — set via `$env:ISERVER_PASSWORD = '...'` before running"
}

# --- SuperMap 原生库 ---
# iobjectspy 的 Java 网关需要 SuperMap bin/ 目录在 PATH 中才能找到 Wrapj*.dll
$env:PATH = "E:\SuperMap\bin;$env:PATH"

# --- Python 环境 ---
$condaPython = "D:\Conda_Data\envs\terroir_hunter\python.exe"
if (-not (Test-Path $condaPython)) {
    Write-Error "terroir_hunter Python not found at $condaPython"
    exit 1
}

$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host "========================================"
Write-Host " 天眼寻珍·苍穹 — 启动"
Write-Host "========================================"
Write-Host "[ENV] GCP_PROJECT_ID = $($env:GCP_PROJECT_ID)"
Write-Host "[ENV] FASTAPI        = http://127.0.0.1:$Port"
Write-Host "[ENV] ISERVER        = $($env:ISERVER_BASE)"
Write-Host "[ROOT] $projectRoot"
Write-Host "========================================"

Push-Location $projectRoot
try {
    & $condaPython server/main.py
}
finally {
    Pop-Location
}
