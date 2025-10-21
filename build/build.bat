@echo off
setlocal enabledelayedexpansion

REM Change to parent directory (where RogueSignalProtocol.py is located)
cd /d "%~dp0.."

REM Build type: alpha (default) or release
set BUILD_TYPE=%1
if "%BUILD_TYPE%"=="" set BUILD_TYPE=alpha

echo Building RogueSignalProtocol (%BUILD_TYPE% mode)...

REM Set log level based on build type
if /i "%BUILD_TYPE%"=="release" (
    set LOG_LEVEL=WARNING
) else (
    set LOG_LEVEL=DEBUG
)

REM Clean previous build
echo Cleaning previous build...
if exist dist rmdir /s /q dist
if exist build\RogueSignalProtocol rmdir /s /q build\RogueSignalProtocol

REM Run PyInstaller
echo Running PyInstaller...
.venv\Scripts\python.exe -m PyInstaller --onefile --clean RogueSignalProtocol.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PyInstaller failed
    pause
    exit /b 1
)

REM Copy assets to dist
echo Copying assets...
copy /Y game_content.json dist\ >nul
copy /Y game_rules.json dist\ >nul
copy /Y story_content.json dist\ >nul
copy /Y arial.ttf dist\ >nul
copy /Y LICENSE dist\ >nul
copy /Y README.txt dist\ >nul
xcopy /E /I /Y /Q graphics dist\graphics >nul
xcopy /E /I /Y /Q sound dist\sound >nul
xcopy /E /I /Y /Q music dist\music >nul

REM Create debug flag for alpha builds
if /i "%BUILD_TYPE%"=="alpha" (
    echo. > dist\debug_mode.flag
)

REM Create release archive
echo Creating release archive...
set TIMESTAMP=%date:~-4%-%date:~-10,2%-%date:~-7,2%
set RELEASE_NAME=RogueSignalProtocol_%BUILD_TYPE%_%TIMESTAMP%.zip
if not exist releases mkdir releases
"C:\Program Files\7-Zip\7z.exe" a -tzip "releases\%RELEASE_NAME%" ".\dist\*" >nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to create zip archive
    pause
    exit /b 1
)

echo.
echo Build complete!
echo Executable: dist\RogueSignalProtocol.exe
echo Archive: releases\%RELEASE_NAME%
