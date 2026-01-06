#!/usr/bin/env python3
import sys
import time
import psycopg2

def wait_for_db():
    db_host = "db"
    db_port = 5432
    db_name = "edrp"
    db_user = "edrp"
    db_password = "edrp2025"
    
    retries = 30
    delay = 2
    
    for attempt in range(retries):
        try:
            conn = psycopg2.connect(
                host=db_host,
                port=db_port,
                database=db_name,
                user=db_user,
                password=db_password
            )
            conn.close()
            print("Database is ready!")
            return True
        except psycopg2.OperationalError as e:
            print(f"Attempt {attempt + 1}: Database not ready - {e}")
            time.sleep(delay)
    
    print("Database never became ready, exiting.")
    return False

if __name__ == "__main__":
    if wait_for_db():
        import subprocess
        import sys
        # Run alembic migrations and then start the main application
        result = subprocess.run(["alembic", "upgrade", "head"])
        if result.returncode == 0:
            # Start the main application
            subprocess.run([sys.executable, "main.py"])
        else:
            print("Failed to run migrations")
            sys.exit(1)
    else:
        sys.exit(1)
