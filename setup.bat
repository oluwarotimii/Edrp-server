@echo off
echo Setting up Education ERP System...
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Create and activate virtual environment
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate

:: Install dependencies
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

:: Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo "=================================================="
    echo "  SETUP INSTRUCTIONS:"
    echo "  1. Open the .env file in a text editor"
    echo "  2. Update the configuration values, especially:"
    echo "     - DATABASE_URL with your PostgreSQL connection string"
    echo "     - SECRET_KEY with a strong random string"
    echo "  3. Save the file"
    echo "  4. Run 'run.bat' to start the application"
    echo "=================================================="
    echo.
    pause
) else (
    echo .env file already exists. Skipping creation.
)

echo.
echo Setup completed successfully!
pause
