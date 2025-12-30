@echo off
setlocal enabledelayedexpansion

REM Create a new version-specific release checklist
REM Usage: new-release.bat [version]
REM Example: new-release.bat 0.9.2

cd /d "%~dp0.."

set VERSION=%1

if "%VERSION%"=="" (
    echo Usage: new-release.bat [version]
    echo Example: new-release.bat 0.9.2
    echo.
    echo This creates a version-specific copy of RELEASE_CHECKLIST.md
    echo to track progress for your release.
    exit /b 1
)

set SOURCE=RELEASE_CHECKLIST.md
set TARGET=RELEASE_CHECKLIST_%VERSION%.md

if not exist "%SOURCE%" (
    echo ERROR: %SOURCE% not found
    exit /b 1
)

if exist "%TARGET%" (
    echo WARNING: %TARGET% already exists
    echo Overwrite? [Y/N]
    set /p CONFIRM=
    if /i not "!CONFIRM!"=="Y" (
        echo Cancelled.
        exit /b 0
    )
)

REM Copy the checklist
copy /Y "%SOURCE%" "%TARGET%" >nul

echo.
echo Created: %TARGET%
echo.
echo Next steps:
echo   1. Open %TARGET% and work through each phase
echo   2. Check off items as you complete them: [ ] to [x]
echo   3. Delete the file when release is complete
echo.
echo Quick reference - key commands for %VERSION%:
echo   Build:    build\build.bat beta %VERSION%
echo   Push:     build\push-all.bat %VERSION%
echo   Notes:    python build\extract-release-notes.py %VERSION%
echo   Validate: python build\validate-release.py
