@echo off
setlocal enabledelayedexpansion

REM ========================================
REM RogueSignalProtocol Build Script
REM ========================================

REM Check for build type argument (default: alpha with debug logging)
set BUILD_TYPE=%1
if "%BUILD_TYPE%"=="" set BUILD_TYPE=alpha

if /i "%BUILD_TYPE%"=="release" (
    echo Building RELEASE version (minimal logging)...
    set LOG_LEVEL=WARNING
    set BUILD_SUFFIX=Release
) else (
    if /i "%BUILD_TYPE%"=="alpha" (
        echo Building ALPHA version (debug logging for playtesters)...
        set LOG_LEVEL=DEBUG
        set BUILD_SUFFIX=Alpha
    ) else (
        echo Unknown build type: %BUILD_TYPE%
        echo Usage: build.bat [alpha^|release]
        echo   alpha   - Debug logging for playtesters (default)
        echo   release - Minimal logging for public release
        pause
        exit /b 1
    )
)

echo.

REM ========================================
REM Verify script is run from build folder
REM ========================================
if not exist "build.bat" (
    echo ERROR: This script must be run from the build\ folder!
    echo Current directory: %CD%
    echo.
    echo Navigate to the build folder first:
    echo   cd build
    echo   build.bat
    pause
    exit /b 1
)

REM Navigate to project root (parent of build folder)
cd ..

REM ========================================
REM VALIDATION: Check required files exist
REM ========================================
echo Checking required files...

set MISSING_FILES=0

if not exist "RogueSignalProtocol.py" (
    echo ERROR: RogueSignalProtocol.py not found!
    set MISSING_FILES=1
)

if not exist "game_content.json" (
    echo ERROR: game_content.json not found!
    set MISSING_FILES=1
)

if not exist "game_rules.json" (
    echo ERROR: game_rules.json not found!
    set MISSING_FILES=1
)

if not exist "graphics_tiles.json" (
    echo ERROR: graphics_tiles.json not found!
    set MISSING_FILES=1
)

if not exist "story_content.json" (
    echo ERROR: story_content.json not found!
    set MISSING_FILES=1
)

if not exist "terminal10x16_gs_ro.png" (
    echo ERROR: terminal10x16_gs_ro.png not found!
    set MISSING_FILES=1
)

if not exist "graphics\" (
    echo ERROR: graphics\ folder not found!
    set MISSING_FILES=1
)

if not exist "sound\" (
    echo ERROR: sound\ folder not found!
    set MISSING_FILES=1
)

if not exist "music\" (
    echo ERROR: music\ folder not found!
    set MISSING_FILES=1
)

if not exist ".venv\Scripts\pyinstaller.exe" (
    echo ERROR: PyInstaller not found in .venv! Run: pip install pyinstaller
    set MISSING_FILES=1
)

if !MISSING_FILES!==1 (
    echo.
    echo *** BUILD ABORTED: Missing required files! ***
    pause
    exit /b 1
)

echo All required files found.
echo.

REM ========================================
REM CLEAN: Remove old build artifacts
REM ========================================
echo Cleaning previous build...

REM Clean PyInstaller temp files
if exist "build\RogueSignalProtocol" rmdir /s /q "build\RogueSignalProtocol"

REM Clean and recreate dist folder (ensures no stale files)
if exist "dist\" (
    rmdir /s /q "dist"
)
mkdir "dist"

echo Clean complete.
echo.

REM ========================================
REM BUILD: Run PyInstaller
REM ========================================
echo Running PyInstaller...

REM Set environment variable for logging level (read by Python code)
set RSP_LOG_LEVEL=!LOG_LEVEL!

REM Check if custom .spec file exists
if exist "RogueSignalProtocol.spec" (
    echo Found existing .spec file, using it...
    .venv\Scripts\pyinstaller.exe RogueSignalProtocol.spec
) else (
    echo Creating new build with default settings...
    REM Add --noconsole to hide console window for graphical game
    REM Remove --noconsole if you need to see Python error messages during development
    .venv\Scripts\pyinstaller.exe --onefile --noconsole --name RogueSignalProtocol RogueSignalProtocol.py

    REM Optional: Delete auto-generated .spec file to keep project clean
    REM Comment this out if you want to customize the .spec file
    if exist "RogueSignalProtocol.spec" del /q "RogueSignalProtocol.spec"
)

REM Create a build_info.txt to indicate build type
echo Build Type: !BUILD_SUFFIX! > "dist\build_info.txt"
echo Log Level: !LOG_LEVEL! >> "dist\build_info.txt"
echo Build Date: %date% %time% >> "dist\build_info.txt"

REM For alpha builds, create debug_mode.flag to enable verbose logging
if /i "!BUILD_TYPE!"=="alpha" (
    echo Creating debug_mode.flag for alpha build...
    echo This file enables DEBUG logging for playtester bug reports. > "dist\debug_mode.flag"
    echo Delete this file to reduce logging to errors only. >> "dist\debug_mode.flag"
)

REM Check if build succeeded
if !ERRORLEVEL! NEQ 0 (
    echo.
    echo *** BUILD FAILED! ***
    echo PyInstaller returned error code !ERRORLEVEL!
    pause
    exit /b !ERRORLEVEL!
)

REM Verify exe was created
if not exist "dist\RogueSignalProtocol.exe" (
    echo.
    echo *** BUILD FAILED! ***
    echo Executable not found in dist folder!
    pause
    exit /b 1
)

echo PyInstaller build successful.
echo.

REM ========================================
REM COPY: Assets to dist folder
REM ========================================
echo Copying assets to dist folder...

REM Copy JSON config files
echo - JSON config files...
copy /Y "game_content.json" "dist\" >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo ERROR: Failed to copy game_content.json
    goto COPY_ERROR
)

copy /Y "game_rules.json" "dist\" >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo ERROR: Failed to copy game_rules.json
    goto COPY_ERROR
)

copy /Y "graphics_tiles.json" "dist\" >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo ERROR: Failed to copy graphics_tiles.json
    goto COPY_ERROR
)

copy /Y "story_content.json" "dist\" >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo ERROR: Failed to copy story_content.json
    goto COPY_ERROR
)

REM Copy font file
echo - Font file...
copy /Y "terminal10x16_gs_ro.png" "dist\" >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo ERROR: Failed to copy terminal10x16_gs_ro.png
    goto COPY_ERROR
)

REM Copy LICENSE if it exists
if exist "LICENSE" (
    echo - LICENSE file...
    copy /Y "LICENSE" "dist\" >nul 2>&1
)

REM Copy README for distribution
echo - Distribution README...
copy /Y "README.txt" "dist\README.txt" >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo ERROR: Failed to copy README.txt
    goto COPY_ERROR
)

REM Copy asset folders (with /H to include hidden files)
echo - Graphics folder...
xcopy /E /I /Y /Q /H "graphics" "dist\graphics" >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo ERROR: Failed to copy graphics folder
    goto COPY_ERROR
)

echo - Sound folder...
xcopy /E /I /Y /Q /H "sound" "dist\sound" >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo ERROR: Failed to copy sound folder
    goto COPY_ERROR
)

echo - Music folder...
xcopy /E /I /Y /Q /H "music" "dist\music" >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo ERROR: Failed to copy music folder
    goto COPY_ERROR
)

echo Asset copy complete.
echo.

REM ========================================
REM ARCHIVE: Create timestamped release
REM ========================================
echo Creating timestamped release archive...

REM Create releases folder if it doesn't exist
if not exist "releases" mkdir "releases"

REM Generate timestamp with seconds (YYYY-MM-DD_HHMMSS format, locale-safe)
for /f "tokens=1-3 delims=/ " %%a in ('echo %date%') do (
    set BUILD_DATE=%%c-%%a-%%b
)

REM Get time including seconds
for /f "tokens=1-4 delims=:. " %%a in ("%time%") do (
    set HH=%%a
    set MM=%%b
    set SS=%%c
)

REM Pad with zeros (handle single-digit hours)
if "!HH:~0,1!"==" " set HH=0!HH:~1,1!
if "!MM:~0,1!"==" " set MM=0!MM:~1,1!
if "!SS:~0,1!"==" " set SS=0!SS:~1,1!

set BUILD_TIME=!HH!!MM!!SS!
set TIMESTAMP=!BUILD_DATE!_!BUILD_TIME!
set RELEASE_NAME=RogueSignalProtocol_!BUILD_SUFFIX!_!TIMESTAMP!.zip

REM Try to create zip with PowerShell
echo Compressing to !RELEASE_NAME!...
powershell -ExecutionPolicy Bypass -Command "try { Compress-Archive -Path 'dist\*' -DestinationPath 'releases\!RELEASE_NAME!' -Force -ErrorAction Stop; exit 0 } catch { Write-Host 'PowerShell zip failed:' $_.Exception.Message; exit 1 }" >nul 2>&1

if !ERRORLEVEL! NEQ 0 (
    echo WARNING: PowerShell compression failed. Skipping archive creation.
    echo You can manually zip the dist\ folder.
    set ARCHIVE_CREATED=0
) else (
    echo Archive created successfully.
    set ARCHIVE_CREATED=1
)

echo.

REM ========================================
REM SUCCESS: Show results
REM ========================================
echo ========================================
echo BUILD SUCCESSFUL!
echo ========================================
echo.
echo Executable: dist\RogueSignalProtocol.exe
if !ARCHIVE_CREATED!==1 (
    echo Release archive: releases\!RELEASE_NAME!
)
echo.
echo The dist\ folder contains everything needed to run the game.
echo You can distribute the entire dist\ folder or the zip file.
echo.
echo IMPORTANT: Test the exe by running it from different folders
echo            to ensure asset loading works correctly!
echo.
pause
exit /b 0

REM ========================================
REM ERROR HANDLERS
REM ========================================
:COPY_ERROR
echo.
echo *** ERROR copying files! ***
echo Check that all source files exist and are readable.
echo Build directory: %CD%
pause
exit /b 1
