$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$standalone = Join-Path $root ".next\standalone"
if (-not (Test-Path $standalone)) {
    throw "Missing .next/standalone - run npm run build first"
}

$staticSrc = Join-Path $root ".next\static"
$staticDst = Join-Path $standalone ".next\static"
if (Test-Path $staticSrc) {
    if (Test-Path $staticDst) { Remove-Item $staticDst -Recurse -Force }
    Copy-Item $staticSrc $staticDst -Recurse -Force
}

$publicSrc = Join-Path $root "public"
$publicDst = Join-Path $standalone "public"
if (Test-Path $publicSrc) {
    if (Test-Path $publicDst) { Remove-Item $publicDst -Recurse -Force }
    Copy-Item $publicSrc $publicDst -Recurse -Force
}
