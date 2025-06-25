@echo off
call venv\Scripts\activate
echo Fixing migration conflicts...
echo.

:: Show current migration status
echo Current migration status:
alembic current

echo.
echo Attempting to resolve multiple heads...

:: Create a merge migration if needed
alembic merge heads -m "merge multiple heads"

:: Run the migrations
alembic upgrade heads

echo.
echo Migration status after fix:
alembic current

echo.
echo If you still see issues, you may need to manually resolve the migrations.
echo 1. Run 'alembic heads' to see all heads
echo 2. Create a merge migration: 'alembic merge -m "merge message" head1 head2'
echo 3. Then run 'alembic upgrade heads'

pause
