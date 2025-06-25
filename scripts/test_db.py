"""Test database connection script"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def test_connection():
    """Test the database connection"""
    load_dotenv()
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ Error: DATABASE_URL not found in .env file")
        return False
    
    try:
        # Add sslmode=require if not present
        if 'sslmode' not in DATABASE_URL:
            if '?' in DATABASE_URL:
                DATABASE_URL += "&sslmode=require"
            else:
                DATABASE_URL += "?sslmode=require"
        
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            print("🔍 Testing database connection...")
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ Successfully connected to PostgreSQL {version}")
            
            # Test if tables exist
            try:
                conn.execute(text("SELECT 1 FROM users LIMIT 1;"))
                print("✅ Users table exists")
            except Exception as e:
                print("⚠️  Users table doesn't exist or is empty. Run migrations first.")
                print(f"   Error: {str(e).split('\n')[0]}")
                
        return True
    except Exception as e:
        print(f"❌ Failed to connect to the database")
        print(f"   Error: {str(e).split('\n')[0]}")
        print("\nTroubleshooting:")
        print("1. Check if your IP is allowlisted in Railway")
        print("2. Verify DATABASE_URL in .env is correct")
        print("3. Ensure the database is running in Railway")
        print("4. Check your internet connection")
        return False

if __name__ == "__main__":
    if test_connection():
        sys.exit(0)
    else:
        sys.exit(1)
