@echo off
setlocal enabledelayedexpansion

REM Push build to itch.io using butler
REM Usage: push-itch.bat [alpha|beta|release] [version]
REM Example: push-itch.bat beta 0.9.1

cd /d "%~dp0.."

set BUILD_TYPE=%1
set VERSION=%2

if "%BUILD_TYPE%"=="" (
    echo Usage: push-itch.bat [alpha^|beta^|release] [version]
    echo Example: push-itch.bat beta 0.9.1
    exit /b 1
)

if "%VERSION%"=="" (
    echo ERROR: Version is required
    echo Usage: push-itch.bat [alpha^|beta^|release] [version]
    exit /b 1
)

REM Find butler (check build\butler first, then PATH)
set BUTLER=
if exist "%~dp0butler\butler.exe" (
    set BUTLER=%~dp0butler\butler.exe
) else (
    where butler >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
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

REM Verify dist folder exists
if not exist dist\RogueSignalProtocol.exe (
    echo ERROR: dist\RogueSignalProtocol.exe not found
    echo Run build.bat first
    exit /b 1
)

REM Set channel based on build type
REM Channels: windows, windows-beta, windows-alpha
if /i "%BUILD_TYPE%"=="release" (
    set CHANNEL=windows
) else ( if /i "%BUILD_TYPE%"=="beta" (
    set CHANNEL=windows-beta
) else ( if /i "%BUILD_TYPE%"=="alpha" (
    set CHANNEL=windows-alpha
) else (
    echo ERROR: Invalid build type. Use: alpha, beta, or release
    exit /b 1
) ) )

set PROJECT=dragynrain/rogue-signal-protocol

echo.
echo Pushing to itch.io...
echo   Project: %PROJECT%
echo   Channel: %CHANNEL%
echo   Version: %VERSION%
echo   Source:  dist/
echo.

REM Push with version tag
"%BUTLER%" push dist "%PROJECT%:%CHANNEL%" --userversion %VERSION%

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: butler push failed
    exit /b 1
)

echo.
echo Push complete!
echo View at: https://dragynrain.itch.io/rogue-signal-protocol
