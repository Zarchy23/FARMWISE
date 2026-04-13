# FarmWise Automation Scheduler Startup Script (PowerShell)
# Use this for Windows Task Scheduler integration
# In Task Scheduler: Set Action → Program/script to: powershell.exe
# Arguments: -ExecutionPolicy Bypass -File C:\Users\Zarchy\farmwise\start_scheduler.ps1

# Set error action preference
$ErrorActionPreference = "Stop"

# Change to FarmWise directory
Set-Location "C:\Users\Zarchy\farmwise"

Write-Host "======================================" -ForegroundColor Green
Write-Host "Starting FarmWise Automation Scheduler" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""

# Activate virtual environment if it exists
if (Test-Path ".\venv\Scripts\Activate.ps1") {
    Write-Host "[*] Activating virtual environment..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"
}

# Start the scheduler
try {
    Write-Host "[*] Starting scheduler..." -ForegroundColor Yellow
    python manage.py runscheduler
}
catch {
    Write-Host "[!] Error starting scheduler:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
