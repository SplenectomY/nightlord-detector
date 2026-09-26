# Build a one-file Windows EXE the same way NightreignArmamentHelper does:
# vendor Tesseract into resources/, then freeze with PyInstaller.
# If Inno Setup (ISCC.exe) is installed, also wrap that EXE in an installer.
#
# From a Developer PowerShell in the repo root:
#   python -m venv .venv
#   .\.venv\Scripts\Activate.ps1
#   pip install -r requirements.txt
#   winget install UB-Mannheim.TesseractOCR
#   winget install JRSoftware.InnoSetup
#   scripts\build_windows.cmd
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\build_windows.ps1
#
# This file is ASCII-only. Windows PowerShell 5.1 misreads UTF-8 dashes as quotes.

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
    $srcResolved = (Resolve-Path $TessSrc).Path
    $dstResolved = $null
    if (Test-Path $TessDst) {
        $dstResolved = (Resolve-Path $TessDst).Path
    }
    if ($srcResolved -ne $dstResolved) {
        robocopy $TessSrc $TessDst /E /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
        if ($LASTEXITCODE -ge 8) {
            throw "robocopy failed copying Tesseract (exit $LASTEXITCODE)"
        }
    }
} else {
    Write-Warning "tesseract.exe not found. The EXE will still build, but OCR needs a system Tesseract or a copy under resources\Tesseract-OCR."
    Write-Warning "Install https://github.com/UB-Mannheim/tesseract/wiki then rerun this script."
}

python -m pip install -q pyinstaller
python -m PyInstaller --noconfirm --clean nightlord-detector.spec
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit $LASTEXITCODE"
}

$Built = Join-Path $Root "dist\nightlord-detector.exe"
if (-not (Test-Path $Built)) {
    throw "PyInstaller finished but dist\nightlord-detector.exe is missing."
}

Write-Host "Portable EXE: $Built"
Write-Host "Copy that single file. No Python or Tesseract install is required on the target PC if Tesseract was bundled."

$IsccCandidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    "${env:LOCALAPPDATA}\Programs\Inno Setup 6\ISCC.exe"
)
$Iscc = $IsccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Iscc) {
    $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($cmd) { $Iscc = $cmd.Source }
}

if ($Iscc) {
    Write-Host "Building installer with $Iscc"
    & $Iscc (Join-Path $Root "scripts\installer.iss")
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup failed with exit $LASTEXITCODE"
    }
    $Setup = Join-Path $Root "dist\NightlordDetectorSetup.exe"
    if (Test-Path $Setup) {
        Write-Host "Installer: $Setup"
    }
} else {
    Write-Host "Inno Setup not found - skipped NightlordDetectorSetup.exe."
    Write-Host "Install it with: winget install JRSoftware.InnoSetup"
}
