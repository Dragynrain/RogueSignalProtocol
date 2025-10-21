@echo off
setlocal enabledelayedexpansion

echo Test starting...

set BUILD_TYPE=%1
if "%BUILD_TYPE%"=="" set BUILD_TYPE=alpha

echo Build type is: %BUILD_TYPE%

if /i "%BUILD_TYPE%"=="release" (
    echo RELEASE MODE
    set LOG_LEVEL=WARNING
) else (
    if /i "%BUILD_TYPE%"=="alpha" (
        echo ALPHA MODE
        set LOG_LEVEL=DEBUG
    ) else (
        echo Unknown: %BUILD_TYPE%
    )
)

echo Log level: %LOG_LEVEL%
echo Test complete
