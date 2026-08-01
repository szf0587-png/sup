param(
    [string]$SuperMapRoot = "E:\SuperMap",
    [string]$DataRoot = "",
    [string]$WorkspaceName = "luonan_3d",
    [switch]$WithOsm,
    [switch]$NoPyramid,
    [switch]$Overwrite
)

$ErrorActionPreference = "Stop"

$python = Join-Path $SuperMapRoot "support\python\python.exe"
$pythonLib = Join-Path $SuperMapRoot "support\PythonLib"
$iobjectspy = Join-Path $SuperMapRoot "bin_python\iobjectspy\iobjectspy-py38_64"
$bin = Join-Path $SuperMapRoot "bin"
$jre = Join-Path $SuperMapRoot "jre"

foreach ($path in @($python, $pythonLib, $iobjectspy, $bin, $jre)) {
    if (-not (Test-Path $path)) {
        throw "Required SuperMap path not found: $path"
    }
}

$env:JAVA_HOME = $jre
$env:JRE_HOME = $jre
$env:PATH = "$bin;$jre\bin;$jre\bin\server;$env:PATH"
$env:PYTHONPATH = "$pythonLib;$iobjectspy"

$scriptPath = Join-Path $PSScriptRoot "prepare_3d_workspace.py"
$arguments = @(
    $scriptPath,
    "--supermap-root", $SuperMapRoot,
    "--workspace-name", $WorkspaceName
)

if ($DataRoot) {
    $arguments += @("--data-root", $DataRoot)
}
if ($WithOsm) {
    $arguments += "--with-osm"
}
if ($NoPyramid) {
    $arguments += "--no-pyramid"
}
if ($Overwrite) {
    $arguments += "--overwrite"
}

Write-Host "[3D] SuperMap root: $SuperMapRoot"
Write-Host "[3D] Python: $python"
Write-Host "[3D] Running workspace preparation..."
& $python @arguments
