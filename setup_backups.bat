@echo off
REM ==========================================================
REM FarmWise Automated Backup Setup - Windows
REM Run this as Administrator to set up Task Scheduler jobs
REM ==========================================================

setlocal enabledelayedexpansion

REM Get the project directory
set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

echo.
echo ========================================
echo FarmWise Backup - Automatic Setup
echo ========================================
echo.
echo Creating Windows Task Scheduler tasks...
echo.

REM Check if running as admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script requires Administrator privileges!
    echo.
    echo Please:
    echo 1. Right-click on Command Prompt or PowerShell
    echo 2. Select "Run as Administrator"
    echo 3. Run this batch file again
    echo.
    pause
    exit /b 1
)

REM Create backup task - Daily at 2:00 AM
echo [Task 1/2] Creating "FarmWise-Backup" task (Daily 2:00 AM)...
schtasks /create /tn "FarmWise-Backup" /tr "%PROJECT_DIR%venv\Scripts\python.exe %PROJECT_DIR%manage.py daily_backup" /sc daily /st 02:00 /f >nul 2>&1
if %errorLevel% equ 0 (
    echo   ✓ Successfully created FarmWise-Backup task
) else (
    echo   ⚠ Task creation returned code %errorLevel% (may already exist)
)

REM Create verification task - Daily at 7:00 AM
echo [Task 2/2] Creating "FarmWise-VerifyBackups" task (Daily 7:00 AM)...
schtasks /create /tn "FarmWise-VerifyBackups" /tr "%PROJECT_DIR%venv\Scripts\python.exe %PROJECT_DIR%manage.py daily_backup --verify" /sc daily /st 07:00 /f >nul 2>&1
if %errorLevel% equ 0 (
    echo   ✓ Successfully created FarmWise-VerifyBackups task
) else (
    echo   ⚠ Task creation returned code %errorLevel% (may already exist)
)

echo.
echo ========================================
echo ✓ Setup Complete!
echo ========================================
echo.
echo Your backups will now run automatically:
echo   • 2:00 AM Daily  - Full backup (database + media + config)
echo   • 7:00 AM Daily  - Verify backup integrity
echo.
echo Backup location: C:\Backups\farmwise\
echo Log file: logs\backup.log
echo.
echo To view scheduled tasks:
echo   - Open Task Scheduler
echo   - Look for tasks starting with "FarmWise-"
echo.
pause
