@echo off
setlocal enabledelayedexpansion

REM Push Windows build to itch.io using butler
REM Usage: push-itch.bat [version]
REM Example: push-itch.bat 0.9.1
REM
REM Expects zip file in releases/ folder named RogueSignalProtocol_beta_[version].zip
REM (or similar naming - script will find the first matching zip)

cd /d "%~dp0.."

set VERSION=%1

if "%VERSION%"=="" (
    echo Usage: push-itch.bat [version]
    echo Example: push-itch.bat 0.9.1
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

set PROJECT=dragynrain/rogue-signal-protocol
set CHANNEL=windows

REM Look for zip file with version in releases/
set ZIP_FILE=
for %%f in (releases\*%VERSION%*.zip) do (
    set ZIP_FILE=%%f
)

if "%ZIP_FILE%"=="" (
    echo ERROR: No zip file containing version %VERSION% found in releases/
    echo Expected something like: releases/RogueSignalProtocol_beta_%VERSION%.zip
    echo Run build.bat first
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
echo Verify at: https://dragynrain.itch.io/rogue-signal-protocol/edit
echo.
echo Check status:
echo   %BUTLER% status %PROJECT%
