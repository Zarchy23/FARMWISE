@echo off
REM FarmWise Automation Scheduler Startup Script
REM This batch file starts the APScheduler for automated task processing
REM Add this to Windows Task Scheduler to run at startup or specific times

setlocal enabledelayedexpansion

REM Navigate to FarmWise directory
cd /d c:\Users\Zarchy\farmwise

REM Activate virtual environment (if using)
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Start the scheduler
echo.
echo ========================================
echo Starting FarmWise Automation Scheduler
echo ========================================
echo.
python manage.py runscheduler

REM If scheduler crashes, wait before exiting
if errorlevel 1 (
    echo.
    echo ERROR: Scheduler failed to start!
    echo Please check the error above.
    pause
    exit /b 1
)

endlocal
