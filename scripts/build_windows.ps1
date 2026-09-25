# Build a one-file Windows EXE the same way NightreignArmamentHelper does:
# vendor Tesseract into resources/, then freeze with PyInstaller.
#
# From a Developer PowerShell in the repo root:
#   python -m venv .venv
#   .\.venv\Scripts\Activate.ps1
#   pip install -r requirements.txt
#   powershell -File scripts\build_windows.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$TessSrcCandidates = @(
    "$env:ProgramFiles\Tesseract-OCR",
    "${env:ProgramFiles(x86)}\Tesseract-OCR",
    "$Root\resources\Tesseract-OCR"
)

$TessSrc = $TessSrcCandidates | Where-Object { Test-Path (Join-Path $_ "tesseract.exe") } | Select-Object -First 1
$TessDst = Join-Path $Root "resources\Tesseract-OCR"

if ($TessSrc) {
    Write-Host "Bundling Tesseract from $TessSrc"
    New-Item -ItemType Directory -Force -Path (Split-Path $TessDst) | Out-Null
    if ((Resolve-Path $TessSrc).Path -ne (Resolve-Path -ErrorAction SilentlyContinue $TessDst).Path) {
        robocopy $TessSrc $TessDst /E /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
    }
} else {
    Write-Warning "tesseract.exe not found. The EXE will still build, but OCR needs a system Tesseract or a copy under resources\Tesseract-OCR."
    Write-Warning "Install https://github.com/UB-Mannheim/tesseract/wiki then rerun this script."
}

python -m pip install -q pyinstaller
python -m PyInstaller --noconfirm --clean nightlord-detector.spec

$Built = Join-Path $Root "dist\nightlord-detector.exe"
if (Test-Path $Built) {
    Write-Host "Built $Built"
    Write-Host "Copy that single file. No Python or Tesseract install required on the target PC if Tesseract was bundled."
} else {
    throw "PyInstaller finished but dist\nightlord-detector.exe is missing."
}
