# Setup environment script for Windows
Write-Host "🚀 Setting up Edrp Server Environment..." -ForegroundColor Cyan

# Check if .env exists, if not create from .env.example
if (-not (Test-Path .env)) {
    Write-Host "ℹ️  Creating .env file from .env.example"
    Copy-Item .env.example .env
    
    # Ask for database URL
    $dbUrl = Read-Host "📝 Enter your Railway PostgreSQL DATABASE_URL"
    
    # Update .env with database URL
    (Get-Content .env) -replace 'DATABASE_URL=.*', "DATABASE_URL=$dbUrl" | Set-Content .env
    
    # Generate a random secret key if not exists
    $secretKey = [System.Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes(32))
    (Get-Content .env) -replace 'SECRET_KEY=.*', "SECRET_KEY=$secretKey" | Set-Content .env
    
    Write-Host "✅ .env file created and configured" -ForegroundColor Green
} else {
    Write-Host "ℹ️  .env file already exists, skipping creation" -ForegroundColor Yellow
}

# Install Python dependencies
Write-Host "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Run database migrations
Write-Host "🔄 Running database migrations..."
alembic upgrade head

# Test database connection
Write-Host "🔍 Testing database connection..."
python -m scripts.test_db

# Create super admin user
$createAdmin = Read-Host "❓ Do you want to create a super admin user? (y/n)"
if ($createAdmin -eq 'y') {
    $email = Read-Host "📧 Enter admin email"
    $password = Read-Host -AsSecureString "🔑 Enter admin password"
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
    $plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    
    python -m scripts.create_admin --email $email --password $plainPassword
}

Write-Host "\n✨ Setup completed!" -ForegroundColor Green
Write-Host "Start the server with: python -m uvicorn main:app --reload" -ForegroundColor Cyan
Write-Host "Access the API docs at: http://localhost:8000/docs" -ForegroundColor Cyan
