@echo off
setlocal enabledelayedexpansion

REM Push all builds to itch.io using butler
REM Usage: push-all.bat [version]
REM Example: push-all.bat 0.9.1
REM
REM Downloads Linux builds from GitHub release if not present locally,
REM then pushes Windows, Linux tarball, and AppImage to itch.io channels.

cd /d "%~dp0.."

set VERSION=%1

if "%VERSION%"=="" (
    echo Usage: push-all.bat [version]
    echo Example: push-all.bat 0.9.1
    exit /b 1
)

REM Find butler (check build\butler first, then PATH)
set BUTLER=
if exist "%~dp0butler\butler.exe" (
    set BUTLER=%~dp0butler\butler.exe
) else (
    where butler >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        set BUTLER=butler
    )
)

if "%BUTLER%"=="" (
    echo ERROR: butler not found
    echo Expected location: build\butler\butler.exe
    echo Or add butler to PATH
    echo Download from: https://itch.io/docs/butler/installing.html
    exit /b 1
)

REM Find GitHub CLI
set GH=
where gh >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set GH=gh
) else ( if exist "C:\Program Files\GitHub CLI\gh.exe" (
    set GH="C:\Program Files\GitHub CLI\gh.exe"
) )

set PROJECT=dragynrain/rogue-signal-protocol

REM Expected filenames
set WIN_ZIP=
for %%f in (releases\*%VERSION%*.zip) do (
    set WIN_ZIP=%%f
)
set TARBALL=releases\RogueSignalProtocol-%VERSION%-Linux.tar.gz
set APPIMAGE=releases\RogueSignalProtocol-%VERSION%-x86_64.AppImage

echo.
echo ======================================
echo Pushing all builds to itch.io
echo Version: %VERSION%
echo ======================================
echo.

REM Check Windows build
if "%WIN_ZIP%"=="" (
    echo ERROR: No Windows zip found for version %VERSION%
    echo Expected in releases\ folder
    echo Run build.bat first: build\build.bat beta %VERSION%
    exit /b 1
)
echo Windows build: %WIN_ZIP%

REM Download Linux builds if not present
if not exist "%TARBALL%" (
    echo Linux tarball not found locally, downloading from GitHub...
    if "%GH%"=="" (
        echo ERROR: GitHub CLI ^(gh^) not found and Linux builds missing
        echo Either install gh or manually download from GitHub release
        exit /b 1
    )
    %GH% release download v%VERSION% --pattern "RogueSignalProtocol-*-Linux.tar.gz" --dir releases/
    if !ERRORLEVEL! NEQ 0 (
        echo ERROR: Failed to download tarball from GitHub
        exit /b 1
    )
)
echo Linux tarball: %TARBALL%

if not exist "%APPIMAGE%" (
    echo AppImage not found locally, downloading from GitHub...
    if "%GH%"=="" (
        echo ERROR: GitHub CLI ^(gh^) not found and Linux builds missing
        echo Either install gh or manually download from GitHub release
        exit /b 1
    )
    %GH% release download v%VERSION% --pattern "RogueSignalProtocol-*-x86_64.AppImage" --dir releases/
    if !ERRORLEVEL! NEQ 0 (
        echo ERROR: Failed to download AppImage from GitHub
        exit /b 1
    )
)
echo Linux AppImage: %APPIMAGE%

echo.
echo ======================================
echo Pushing to itch.io channels...
echo ======================================
echo.

REM Push Windows
echo [1/3] Pushing Windows build to 'windows' channel...
"%BUTLER%" push "%WIN_ZIP%" "%PROJECT%:windows" --userversion %VERSION%
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Windows push failed
    exit /b 1
)
echo.

REM Push Linux tarball
echo [2/3] Pushing Linux tarball to 'linux' channel...
"%BUTLER%" push "%TARBALL%" "%PROJECT%:linux" --userversion %VERSION%
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Linux tarball push failed
    exit /b 1
)
echo.

REM Push AppImage
echo [3/3] Pushing AppImage to 'linux-appimage' channel...
"%BUTLER%" push "%APPIMAGE%" "%PROJECT%:linux-appimage" --userversion %VERSION%
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: AppImage push failed
    exit /b 1
)

echo.
echo ======================================
echo All pushes complete!
echo ======================================
echo.
echo Verify at: https://dragynrain.itch.io/rogue-signal-protocol/edit
echo.
echo Channel status:
"%BUTLER%" status %PROJECT%
