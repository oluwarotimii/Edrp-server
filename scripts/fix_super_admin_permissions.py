import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError
from dotenv import load_dotenv

# Add project root to path to allow imports from other directories
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fix_super_admin_permissions():
    """
    Connects to the database and grants all available permissions to the 'Super Admin' role.
    If the primary table name is not found, it queries and lists all available tables.
    """
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("ERROR: DATABASE_URL not found in your .env file.")
        print("Please ensure your .env file is correctly configured.")
        return

    print("Connecting to the database...")
    try:
        engine = create_engine(database_url)
        connection = engine.connect()
        print("Connection successful.")
    except Exception as e:
        print(f"ERROR: Failed to connect to the database.\n{e}")
        return

    # We explicitly use 'public.role_permissions' to avoid schema search_path issues.
    # The previous error was confusing because the table *does* exist, but wasn't in the default search path.
    target_table = 'public.role_permissions'

    sql_query = text(f"""
    INSERT INTO {target_table} (role_id, permission_id, created_at, updated_at)
    SELECT
      (SELECT id FROM roles WHERE name = 'Super Admin') as role_id,
      p.id as permission_id,
      NOW(),
      NOW()
    FROM permissions p
    LEFT JOIN {target_table} rp ON rp.permission_id = p.id AND rp.role_id = (SELECT id FROM roles WHERE name = 'Super Admin')
    WHERE rp.permission_id IS NULL;
    """)

    try:
        print(f"Attempting to grant permissions using table '{target_table}'...")
        with connection.begin() as transaction:
            result = connection.execute(sql_query)
            transaction.commit()
            print("\nSUCCESS! Super Admin permissions have been updated.")
            if result.rowcount > 0:
                print(f"{result.rowcount} new permission(s) were granted.")
            else:
                print("No new permissions needed to be granted.")
            print("\nPlease log out and log back in to your application to get a new access token.")

    except ProgrammingError as e:
        # This block runs if the table name was wrong.
        if f'relation "{target_table}" does not exist' in str(e):
            print(f"\nERROR: The table '{target_table}' does not exist in your database.")
            print("This means your database schema is out of sync with your code.")
            print("\nQuerying the database to find the correct table name...")
            
            try:
                # Get the actual list of tables from your database.
                list_tables_query = text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
                tables_result = connection.execute(list_tables_query)
                all_tables = [row[0] for row in tables_result]
                
                print("\n*** DATABASE TABLES FOUND ***")
                for table in all_tables:
                    print(f"- {table}")
                print("***************************")
                print("\nPlease inspect the list above to find the correct table for role permissions.")
                print("It might be named 'role_permission' or something similar.")
                print("Once you find it, please let me know the correct name.")

            except Exception as query_e:
                print(f"\nERROR: Could not retrieve table list from the database.\n{query_e}")
        else:
            print(f"\nAn unexpected database error occurred:\n{e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred:\n{e}")
    finally:
        connection.close()

if __name__ == "__main__":
    fix_super_admin_permissions()
