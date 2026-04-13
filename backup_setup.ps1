# backup_setup.ps1 - Set up automated backups on Windows
# Usage: powershell -ExecutionPolicy Bypass -File backup_setup.ps1

# Requires admin privileges
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "ERROR: This script requires admin privileges" -ForegroundColor Red
    exit 1
}

$ProjectPath = "C:\Users\Zarchy\farmwise"
$BackupDir = "C:\Backups\farmwise"
$LogFile = "$ProjectPath\logs\backup_setup.log"

Write-Host "Starting FarmWise backup setup on Windows..." -ForegroundColor Green

# Create backup directory
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    Write-Host "✓ Created backup directory: $BackupDir"
}

# Create logs directory
$LogsDir = "$ProjectPath\logs"
if (-not (Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null
}

# Function to log messages
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Tee-Object -FilePath $LogFile -Append
}

Write-Log "Backup setup started"

# Create backup script
$BackupScript = "$ProjectPath\scripts\backup_database.ps1"

# Create scripts directory
if (-not (Test-Path "$ProjectPath\scripts")) {
    New-Item -ItemType Directory -Path "$ProjectPath\scripts" -Force | Out-Null
}

$BackupScriptContent = @"
# backup_database.ps1 - Backup FarmWise database
# This script is called by Windows Task Scheduler

`$ProjectPath = "$ProjectPath"
`$BackupDir = "$BackupDir"
`$LogFile = "`$ProjectPath\logs\backup.log"
`$DbName = "farmwise_prod"
`$DbUser = "farmwise_user"
`$DbHost = "localhost"

`$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
`$BackupFile = "`$BackupDir\farmwise_db_`$Timestamp.sql.gz"

function Write-Log {
    param([string]`$Message)
    `$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "`$ts - `$Message" | Tee-Object -FilePath `$LogFile -Append
}

Write-Log "Database backup started"

try {
    # Push to project directory
    Push-Location `$ProjectPath
    
    # Activate virtual environment
    & "venv\Scripts\Activate.ps1"
    
    # Run backup manager
    python -m core.backup_manager
    
    if (`$LASTEXITCODE -eq 0) {
        Write-Log "✓ Backup completed successfully"
    } else {
        Write-Log "✗ Backup failed with exit code `$LASTEXITCODE"
        # Send email alert
        `$EmailParams = @{
            To = "admin@farmwise.com"
            From = "backup@farmwise.com"
            Subject = "ALERT: FarmWise Backup Failed"
            Body = "Backup failed on `$(hostname) at `$(Get-Date)"
            SmtpServer = "mail.farmwise.com"
        }
        Send-MailMessage @EmailParams -ErrorAction SilentlyContinue
    }
} catch {
    Write-Log "✗ Error: `$_"
    exit 1
} finally {
    Pop-Location
}
"@

Set-Content -Path $BackupScript -Value $BackupScriptContent
Write-Log "✓ Created backup script: $BackupScript"

# Create verification script
$VerifyScript = "$ProjectPath\scripts\verify_backups.ps1"

$VerifyScriptContent = @"
# verify_backups.ps1 - Verify FarmWise backups

`$BackupDir = "$BackupDir"
`$LogFile = "$ProjectPath\logs\backup_verify.log"
`$MinSize = 1MB
`$MaxAge = 25  # hours

function Write-Log {
    param([string]`$Message)
    `$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "`$ts - `$Message" | Tee-Object -FilePath `$LogFile -Append
}

Write-Log "Backup verification started"

# Check latest database backup
`$LatestDb = Get-ChildItem `$BackupDir -Filter "farmwise_db_*.sql.gz" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if (-not `$LatestDb) {
    Write-Log "✗ No database backup found!"
    exit 1
}

# Check size
if (`$LatestDb.Length -lt `$MinSize) {
    Write-Log "✗ Database backup suspiciously small: `$(`$LatestDb.Length) bytes"
    exit 1
}

# Check age
`$Age = (Get-Date) - `$LatestDb.LastWriteTime
if (`$Age.TotalHours -gt `$MaxAge) {
    Write-Log "✗ Database backup too old: `$([Math]::Round(`$Age.TotalHours)) hours"
    exit 1
}

Write-Log "✓ Backup verification successful"
Write-Log "  Latest backup: `$(`$LatestDb.Name)"
Write-Log "  Size: `$([Math]::Round(`$LatestDb.Length / 1MB)) MB"
Write-Log "  Age: `$([Math]::Round(`$Age.TotalHours)) hours"

# Check disk space
`$Drive = Get-Item `$BackupDir.Substring(0, 1)
`$DiskUsage = `$Drive.TotalSize - `$Drive.AvailableFreeSpace

if ((`$DiskUsage / `$Drive.TotalSize) * 100 -gt 80) {
    Write-Log "⚠️  Disk usage critical!"
    exit 1
}

exit 0
"@

Set-Content -Path $VerifyScript -Value $VerifyScriptContent
Write-Log "✓ Created verification script: $VerifyScript"

# Create scheduled task for databases backup
Write-Host "Creating Windows Task Scheduler tasks..." -ForegroundColor Yellow

$TaskName = "FarmWise-DatabaseBackup"
$TaskDescription = "FarmWise automated database backup"

# Remove existing task if present
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Log "Removed existing task: $TaskName"
}

# Create task
$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$BackupScript`""

$Trigger = New-ScheduledTaskTrigger `
    -Daily `
    -At 2:00AM

$Principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Principal $Principal `
    -Settings $Settings `
    -Description $TaskDescription `
    -Force | Out-Null

Write-Log "✓ Created scheduled task: $TaskName (Daily at 2:00 AM)"

# Create verification task
$VerifyTaskName = "FarmWise-VerifyBackups"

if (Get-ScheduledTask -TaskName $VerifyTaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $VerifyTaskName -Confirm:$false
}

$VerifyAction = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$VerifyScript`""

$VerifyTrigger = New-ScheduledTaskTrigger `
    -Daily `
    -At 7:00AM

Register-ScheduledTask `
    -TaskName $VerifyTaskName `
    -Action $VerifyAction `
    -Trigger $VerifyTrigger `
    -Principal $Principal `
    -Settings $Settings `
    -Description "FarmWise backup verification" `
    -Force | Out-Null

Write-Log "✓ Created scheduled task: $VerifyTaskName (Daily at 7:00 AM)"

# Display summary
Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "✓ Backup setup complete!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "Scheduled tasks created:" -ForegroundColor Cyan
Write-Host "  1. FarmWise-DatabaseBackup (2:00 AM daily)"
Write-Host "  2. FarmWise-VerifyBackups (7:00 AM daily)"
Write-Host ""
Write-Host "Backup location:" -ForegroundColor Cyan
Write-Host "  $BackupDir"
Write-Host ""
Write-Host "Log files:" -ForegroundColor Cyan
Write-Host "  $ProjectPath\logs\backup.log"
Write-Host "  $ProjectPath\logs\backup_verify.log"
Write-Host ""
Write-Host "View scheduled tasks:" -ForegroundColor Cyan
Write-Host "  - Open Task Scheduler"
Write-Host "  - Look for tasks starting with 'FarmWise-'"
Write-Host ""
Write-Host "Manual backup command:" -ForegroundColor Cyan
Write-Host "  cd $ProjectPath"
Write-Host "  python -m core.backup_manager"
Write-Host ""

Write-Log "Setup completed successfully"
