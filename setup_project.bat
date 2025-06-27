@echo off
echo =================================================
echo  Setting up the Education ERP Backend Project
echo =================================================

REM Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH. Please install Python 3.10 or higher.
    goto:eof
)

REM --- Step 1: Create Virtual Environment ---
if not exist venv (
    echo.
    echo --- Creating Python virtual environment...
    python -m venv venv
) else (
    echo.
    echo --- Virtual environment already exists.
)

REM --- Step 2: Activate Virtual Environment and Install Dependencies ---
echo.
echo --- Activating virtual environment and installing dependencies...
call venv\Scripts\activate
pip install -r requirements.txt

REM --- Step 3: Create .env file ---
if not exist .env (
    echo.
    echo --- Creating .env file from .env.example...
    copy .env.example .env
    echo.
    echo.
    echo *******************************************************************
    echo *  ACTION REQUIRED: Please edit the newly created .env file       *
    echo *  and set your PostgreSQL DATABASE_URL.                          *
    echo *  Example: DATABASE_URL="postgresql://user:pass@host:port/dbname" *
    echo *******************************************************************
    echo.
    pause
) else (
    echo.
    echo --- .env file already exists.
)

REM --- Step 4: Run Database Migrations ---
echo.
echo --- Running database migrations...
alembic upgrade head

echo.
echo =================================================
echo  Setup Complete!
echo =================================================
echo.
echo To run the server, use the following command:
echo   uvicorn main:app --reload
echo.
