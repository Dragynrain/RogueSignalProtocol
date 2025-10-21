@echo off
REM ========================================
REM Clean Build Artifacts
REM Safely removes build outputs without
REM deleting the build/ folder itself
REM ========================================

echo Cleaning build artifacts...
echo.

cd ..

set FILES_CLEANED=0

REM Clean PyInstaller temporary files
if exist "build\RogueSignalProtocol" (
    echo Removing PyInstaller temp files...
    rmdir /s /q "build\RogueSignalProtocol"
    set FILES_CLEANED=1
)

if exist "RogueSignalProtocol.spec" (
    echo Removing spec file...
    del /q "RogueSignalProtocol.spec"
    set FILES_CLEANED=1
)

REM Clean dist folder
if exist "dist" (
    echo Cleaning dist folder...
    rmdir /s /q "dist"
    set FILES_CLEANED=1
)

REM Optional: Uncomment to clean releases folder
REM if exist "releases" (
REM     echo Cleaning releases folder...
REM     rmdir /s /q "releases"
REM     set FILES_CLEANED=1
REM )

echo.
if %FILES_CLEANED%==1 (
    echo Clean complete!
) else (
    echo Nothing to clean - all build artifacts already removed.
)
echo.
pause
