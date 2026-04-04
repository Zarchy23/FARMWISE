# FarmWise Database Setup Script with Password and Permissions
# This PowerShell script creates the PostgreSQL database, user, and sets permissions

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FarmWise Database Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if PostgreSQL is installed and running
Write-Host "[1/5] Checking PostgreSQL installation..." -ForegroundColor Yellow
try {
    $psqlPath = Get-Command psql -ErrorAction SilentlyContinue
    if ($psqlPath) {
        Write-Host "✓ PostgreSQL found at: $($psqlPath.Source)" -ForegroundColor Green
    } else {
        Write-Host "✗ PostgreSQL not found in PATH" -ForegroundColor Red
        Write-Host "Please install PostgreSQL from: https://www.postgresql.org/download/windows/" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "✗ Error checking PostgreSQL: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 2: Get PostgreSQL admin password
Write-Host "[2/5] PostgreSQL Admin Credentials" -ForegroundColor Yellow
Write-Host "Enter the password for 'postgres' superuser (set during PostgreSQL installation)" -ForegroundColor Gray
$pgPassword = Read-Host "PostgreSQL password"
Write-Host ""

# Step 3: Create user and set password
Write-Host "[3/5] Creating/Setting up PostgreSQL user..." -ForegroundColor Yellow
try {
    $env:PGPASSWORD = $pgPassword
    
    # Create user with password (ignore if already exists)
    Write-Host "Setting password for 'postgres' user..." -ForegroundColor Gray
    $alterUserSQL = "ALTER USER postgres WITH PASSWORD 'farmwise_secure_password_2024';"
    
    $alterUserSQL | psql -U postgres -h localhost
    
    Write-Host "✓ User password set successfully!" -ForegroundColor Green
    
    Remove-Item env:PGPASSWORD -ErrorAction SilentlyContinue
} catch {
    Write-Host "⚠ Warning setting user password: $_" -ForegroundColor Yellow
}
Write-Host ""

# Step 4: Create database
Write-Host "[4/5] Creating FarmWise database and PostGIS extensions..." -ForegroundColor Yellow
try {
    $env:PGPASSWORD = "farmwise_secure_password_2024"
    
    # Create database
    Write-Host "Creating database..." -ForegroundColor Gray
    psql -U postgres -h localhost -c "CREATE DATABASE farmwise_db ENCODING 'UTF8' OWNER postgres;"
    
    # Run setup SQL script on the new database
    Write-Host "Setting up extensions and permissions..." -ForegroundColor Gray
    psql -U postgres -h localhost -d farmwise_db -f setup_database.sql
    
    Write-Host "✓ Database created with PostGIS extensions!" -ForegroundColor Green
    
    Remove-Item env:PGPASSWORD -ErrorAction SilentlyContinue
} catch {
    Write-Host "⚠ Database may already exist or error occurred: $_" -ForegroundColor Yellow
    Write-Host "Continuing with migrations..." -ForegroundColor Yellow
}
Write-Host ""

# Step 5: Run Django migrations
Write-Host "[5/5] Running Django migrations..." -ForegroundColor Yellow
try {
    python manage.py migrate
    Write-Host "✓ Django migrations completed!" -ForegroundColor Green
} catch {
    Write-Host "✗ Error running migrations: $_" -ForegroundColor Red
    Write-Host "Verify database credentials in .env file" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Success message
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Database setup complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Database Credentials:" -ForegroundColor Cyan
Write-Host "  Database: farmwise_db" -ForegroundColor White
Write-Host "  User: postgres" -ForegroundColor White
Write-Host "  Password: farmwise_secure_password_2024" -ForegroundColor White
Write-Host "  Host: localhost" -ForegroundColor White
Write-Host "  Port: 5432" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Create a superuser: python manage.py createsuperuser" -ForegroundColor White
Write-Host "2. Start development server: python manage.py runserver" -ForegroundColor White
Write-Host "3. Access admin: http://localhost:8000/admin/" -ForegroundColor White
Write-Host ""
