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

REM Verify dist folder exists (build must have run)
if not exist dist\RogueSignalProtocol.exe (
    echo ERROR: dist\RogueSignalProtocol.exe not found
    echo Run build.bat %BUILD_TYPE% first
    exit /b 1
)

REM Channel is always "windows" - we use version tags to distinguish releases
REM (itch.io doesn't use separate channels for alpha/beta/release)
if /i "%BUILD_TYPE%"=="release" (
    set CHANNEL=windows
) else ( if /i "%BUILD_TYPE%"=="beta" (
    set CHANNEL=windows
) else ( if /i "%BUILD_TYPE%"=="alpha" (
    set CHANNEL=windows
) else (
    echo ERROR: Invalid build type. Use: alpha, beta, or release
    exit /b 1
) ) )

set PROJECT=dragynrain/rogue-signal-protocol

REM Build zip filename: RogueSignalProtocol_[type]_[version].zip
set ZIP_FILE=releases\RogueSignalProtocol_%BUILD_TYPE%_%VERSION%.zip

REM Verify zip file exists
if not exist "%ZIP_FILE%" (
    echo ERROR: %ZIP_FILE% not found
    echo Run build.bat %BUILD_TYPE% first, then rename the zip to include version
    echo Expected: RogueSignalProtocol_%BUILD_TYPE%_%VERSION%.zip
    exit /b 1
)

echo.
echo Pushing to itch.io...
echo   Project: %PROJECT%
echo   Channel: %CHANNEL%
echo   Version: %VERSION%
echo   Source:  %ZIP_FILE%
echo.

REM Push zip file with version tag
"%BUTLER%" push "%ZIP_FILE%" "%PROJECT%:%CHANNEL%" --userversion %VERSION%

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: butler push failed
    exit /b 1
)

echo.
echo Push complete!
echo View at: https://dragynrain.itch.io/rogue-signal-protocol
