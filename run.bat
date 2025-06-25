@echo off
call venv\Scripts\activate
echo Starting Education ERP System...
echo.

:: Check if migrations folder exists
if not exist migrations (
    echo Initializing new migrations...
    alembic init migrations
    
    echo Creating initial migration...
    alembic revision --autogenerate -m "Initial migration"
)

echo Running database migrations...
alembic upgrade head
echo.
echo Starting server...
uvicorn main:app --reload
pause
