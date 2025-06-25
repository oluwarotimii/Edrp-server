@echo off
call venv\Scripts\activate
echo Starting Education ERP System...
echo.
echo Running database migrations...
alembic upgrade heads
echo.
echo Starting server...
uvicorn main:app --reload
pause
