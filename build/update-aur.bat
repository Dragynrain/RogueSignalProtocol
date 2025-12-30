@echo off
setlocal enabledelayedexpansion

REM Update AUR package for a new release
REM Usage: update-aur.bat [version] [type]
REM Example: update-aur.bat 0.9.2 beta
REM
REM This script:
REM   1. Updates PKGBUILD with new version and SHA256
REM   2. Generates .SRCINFO using Docker
REM   3. Copies files to AUR repo directory (if it exists)

cd /d "%~dp0.."

set VERSION=%1
set TYPE=%2

if "%VERSION%"=="" (
    echo Usage: update-aur.bat [version] [type]
    echo Example: update-aur.bat 0.9.2 beta
    echo.
    echo type can be: alpha, beta, or release ^(empty for stable^)
    exit /b 1
)

if "%TYPE%"=="" set TYPE=release

REM Calculate version formats
REM pkgver: 0.9.2_beta (underscore for AUR)
REM _vertag: 0.9.2-beta (hyphen for GitHub tag)
if "%TYPE%"=="release" (
    set PKGVER=%VERSION%
    set VERTAG=%VERSION%
) else (
    set PKGVER=%VERSION%_%TYPE%
    set VERTAG=%VERSION%-%TYPE%
)

echo.
echo ======================================
echo AUR Package Update
echo ======================================
echo Version: %VERSION%
echo Type: %TYPE%
echo pkgver: %PKGVER%
echo _vertag: %VERTAG%
echo ======================================
echo.

REM Expected tarball location
set TARBALL=releases\RogueSignalProtocol-%VERTAG%-Linux.tar.gz
set PKGBUILD=packaging\linux\PKGBUILD

REM Check if tarball exists locally, if not try to download
if not exist "%TARBALL%" (
    echo Tarball not found locally, attempting download from GitHub...

    REM Find GitHub CLI
    set GH=
    where gh >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        set GH=gh
    ) else ( if exist "C:\Program Files\GitHub CLI\gh.exe" (
        set GH="C:\Program Files\GitHub CLI\gh.exe"
    ) )

    if "!GH!"=="" (
        echo ERROR: GitHub CLI ^(gh^) not found and tarball not available locally
        echo Either download the tarball manually or install gh
        exit /b 1
    )

    !GH! release download v%VERTAG% --pattern "RogueSignalProtocol-*-Linux.tar.gz" --dir releases/
    if !ERRORLEVEL! NEQ 0 (
        echo ERROR: Failed to download tarball from GitHub release v%VERTAG%
        exit /b 1
    )
)

if not exist "%TARBALL%" (
    echo ERROR: Tarball still not found: %TARBALL%
    exit /b 1
)

echo Found tarball: %TARBALL%

REM Calculate SHA256
echo Calculating SHA256...
for /f "skip=1 tokens=*" %%h in ('certutil -hashfile "%TARBALL%" SHA256') do (
    if not defined SHA256 set SHA256=%%h
)

REM Remove spaces from hash (certutil adds them on some Windows versions)
set SHA256=%SHA256: =%

echo SHA256: %SHA256%
echo.

REM Update PKGBUILD
echo Updating PKGBUILD...

REM Read current PKGBUILD and update version lines
REM Use PowerShell for reliable text replacement
powershell -NoProfile -Command ^
    "$content = Get-Content '%PKGBUILD%' -Raw; " ^
    "$content = $content -replace 'pkgver=[^\r\n]+', 'pkgver=%PKGVER%'; " ^
    "$content = $content -replace '_vertag=[^\r\n]+', '_vertag=%VERTAG%'; " ^
    "$content = $content -replace \"sha256sums=\('[^']+'\)\", \"sha256sums=('%SHA256%')\"; " ^
    "$content | Set-Content '%PKGBUILD%' -NoNewline"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to update PKGBUILD
    exit /b 1
)

echo PKGBUILD updated successfully

REM Convert to Unix line endings (important for AUR)
echo Converting to Unix line endings...
powershell -NoProfile -Command ^
    "$content = Get-Content '%PKGBUILD%' -Raw; " ^
    "$content = $content -replace \"`r`n\", \"`n\"; " ^
    "[System.IO.File]::WriteAllText('%PKGBUILD%', $content)"

REM Also convert .install file
powershell -NoProfile -Command ^
    "$f = 'packaging\linux\rogue-signal-protocol-bin.install'; " ^
    "if (Test-Path $f) { " ^
    "  $c = Get-Content $f -Raw; " ^
    "  $c = $c -replace \"`r`n\", \"`n\"; " ^
    "  [System.IO.File]::WriteAllText($f, $c) " ^
    "}"

REM Generate .SRCINFO using Docker
echo.
echo Generating .SRCINFO using Docker...

REM Check if Docker is available
where docker >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Docker not found, skipping .SRCINFO generation
    echo You will need to generate .SRCINFO manually on a Linux system:
    echo   cd packaging/linux ^&^& makepkg --printsrcinfo ^> .SRCINFO
    goto :skip_srcinfo
)

REM Run makepkg in Arch Linux container
docker run --rm -v "%CD%\packaging\linux://pkg" -w //pkg archlinux ^
    bash -c "pacman -Sy --noconfirm base-devel >/dev/null 2>&1 && useradd -m builder && su builder -c 'makepkg --printsrcinfo'" > packaging\linux\.SRCINFO

if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Docker command failed
    echo You may need to generate .SRCINFO manually
) else (
    echo .SRCINFO generated successfully
)

:skip_srcinfo

REM Check if AUR repo directory exists
set AUR_DIR=D:\Projects\aur-rogue-signal-protocol-bin
if exist "%AUR_DIR%" (
    echo.
    echo Copying files to AUR repo: %AUR_DIR%
    copy /Y packaging\linux\PKGBUILD "%AUR_DIR%\" >nul
    copy /Y packaging\linux\.SRCINFO "%AUR_DIR%\" >nul
    copy /Y packaging\linux\rogue-signal-protocol-bin.install "%AUR_DIR%\" >nul
    echo Files copied to AUR repo
    echo.
    echo To push to AUR:
    echo   cd %AUR_DIR%
    echo   git add PKGBUILD .SRCINFO rogue-signal-protocol-bin.install
    echo   git commit -m "Update to %VERTAG%"
    echo   git push origin master
) else (
    echo.
    echo AUR repo not found at %AUR_DIR%
    echo To clone and push manually:
    echo   git clone ssh://aur@aur.archlinux.org/rogue-signal-protocol-bin.git %AUR_DIR%
    echo   copy packaging\linux\PKGBUILD %AUR_DIR%\
    echo   copy packaging\linux\.SRCINFO %AUR_DIR%\
    echo   copy packaging\linux\rogue-signal-protocol-bin.install %AUR_DIR%\
    echo   cd %AUR_DIR% ^&^& git add -A ^&^& git commit -m "Update to %VERTAG%" ^&^& git push
)

echo.
echo ======================================
echo AUR update preparation complete!
echo ======================================
echo.
echo Updated files:
echo   - packaging\linux\PKGBUILD
echo   - packaging\linux\.SRCINFO
echo.
echo Verify at: https://aur.archlinux.org/packages/rogue-signal-protocol-bin
