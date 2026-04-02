@echo off
setlocal enabledelayedexpansion

REM Change to parent directory (where RogueSignalProtocol.py is located)
cd /d "%~dp0.."

REM Build type: release (default), alpha, or beta
REM - alpha/beta: DEBUG logging enabled (creates debug_mode.flag)
REM - release: Minimal logging (no flag file)
set BUILD_TYPE=%1
if "%BUILD_TYPE%"=="" set BUILD_TYPE=release

REM Version: optional, defaults to date-based naming
REM Usage: build.bat release 1.0.0
set VERSION=%2

echo Building RogueSignalProtocol (%BUILD_TYPE% mode)...

REM Generate wiki documentation from game data
echo Generating wiki documentation...
.venv\Scripts\python.exe docs\generate_wiki.py
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Wiki generation failed - continuing with build
)

REM Clean previous build
echo Cleaning previous build...
if exist dist rmdir /s /q dist
if exist build\RogueSignalProtocol rmdir /s /q build\RogueSignalProtocol

REM Run PyInstaller
echo Running PyInstaller...
.venv\Scripts\python.exe -m PyInstaller --clean RogueSignalProtocol.spec
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PyInstaller failed
    pause
    exit /b 1
)

REM Copy assets to dist
echo Copying assets...
copy /Y game_content.json dist\ >nul
copy /Y game_rules.json dist\ >nul
copy /Y narrative_content.json dist\ >nul
copy /Y graphics_tiles.json dist\ >nul
copy /Y default_bindings.json dist\ >nul
copy /Y KreativeSquare.ttf dist\ >nul
copy /Y logo.png dist\ >nul
copy /Y LICENSE dist\ >nul
copy /Y README.txt dist\ >nul
xcopy /E /I /Y /Q graphics dist\graphics >nul
xcopy /E /I /Y /Q sound dist\sound >nul
xcopy /E /I /Y /Q music dist\music >nul

REM Create debug flag for alpha/beta builds (enables DEBUG logging)
if /i "%BUILD_TYPE%"=="alpha" (
    echo Debug mode enabled for alpha build > dist\debug_mode.flag
) else ( if /i "%BUILD_TYPE%"=="beta" (
    echo Debug mode enabled for beta build > dist\debug_mode.flag
) )

REM Create release archive
echo Creating release archive...
if not exist releases mkdir releases

REM Use version if provided, otherwise fall back to date-based naming
if "%VERSION%"=="" (
    REM Use PowerShell for locale-independent date format (YYYY-MM-DD)
    for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set TIMESTAMP=%%i
    set RELEASE_NAME=RogueSignalProtocol_%BUILD_TYPE%_!TIMESTAMP!.zip
) else (
    set RELEASE_NAME=RogueSignalProtocol_%BUILD_TYPE%_%VERSION%.zip
)

"C:\Program Files\7-Zip\7z.exe" a -tzip "releases\%RELEASE_NAME%" ".\dist\*" >nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to create zip archive
    pause
    exit /b 1
)

REM Generate SHA256 checksum
echo Generating SHA256 checksum...
certutil -hashfile "releases\%RELEASE_NAME%" SHA256 | findstr /v ":" > "releases\%RELEASE_NAME%.sha256"

echo.
echo Build complete!
echo Executable: dist\RogueSignalProtocol.exe
echo Archive: releases\%RELEASE_NAME%
echo Checksum: releases\%RELEASE_NAME%.sha256
