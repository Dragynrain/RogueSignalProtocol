# Windows Batch & PowerShell Reference

## Batch File Syntax Rules

**Critical Limitations:**
- **NO `else if` support!** Batch files don't have `else if` syntax
- Use nested `if` statements instead: `) else ( if ... )`

**Best Practices:**
- Use `%~dp0` to get batch file's directory for reliable path handling
- Prefer `Python -m PyInstaller` over direct `.exe` calls (more reliable)
- Use full Windows paths (D:\...), not relative paths
- Files from `git show` have LF line endings - run `unix2dos` if needed

**Example:**
```batch
@echo off
set BUILD_TYPE=%1

REM ✗ WRONG - else if doesn't exist
if "%BUILD_TYPE%"=="alpha" (
    echo ALPHA
) else if "%BUILD_TYPE%"=="release" (
    echo RELEASE
)

REM ✓ CORRECT - nested if statements
if "%BUILD_TYPE%"=="alpha" (
    echo ALPHA
) else (
    if "%BUILD_TYPE%"=="release" (
        echo RELEASE
    ) else (
        echo UNKNOWN
    )
)
```

## Testing Batch Files from Bash

**NEVER commit .bat files without testing them first!**

**Test method:**
```bash
powershell.exe -Command "Start-Process -FilePath 'cmd.exe' \
  -ArgumentList '/c','D:\Projects\RogueSignalProtocol\path\to\file.bat','args' \
  -Wait -NoNewWindow \
  -RedirectStandardOutput 'D:\Projects\RogueSignalProtocol\stdout.txt' \
  -RedirectStandardError 'D:\Projects\RogueSignalProtocol\stderr.txt'"
cat stdout.txt stderr.txt
```

Replace `path\to\file.bat` and `args` with actual values.

## PowerShell Limitations

**Archive Creation:**
- `Compress-Archive` cmdlet **doesn't work reliably** for this project
- Must use 7zip instead: `C:\Program Files\7-Zip\7z.exe`
- This is a hard dependency for the build process

## Verification Rules

1. **Never assume** - always verify
2. **Never commit blindly** - test first
3. **Never claim "it works"** without proof
4. **Never make multiple commits** without testing each one
5. If you can't test it, say so - don't pretend
