#!/usr/bin/env python3
"""
Setup script for Education ERP Server
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(command, cwd=None):
    """Run a shell command and return its output"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            check=True,
            text=True,
            capture_output=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e.stderr}")
        sys.exit(1)

def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n🔍 Checking dependencies...")
    try:
        import sqlalchemy
        import alembic
        import uvicorn
        print("✅ All required Python packages are installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e.name}")
        print("Please install the required packages with:")
        print("  pip install -r requirements.txt")
        sys.exit(1)

def setup_environment():
    """Set up the environment"""
    print("\n⚙️  Setting up environment...")
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        print("ℹ️  Creating .env file from .env.example")
        env_example = Path(".env.example")
        if not env_example.exists():
            print("❌ Error: .env.example not found")
            sys.exit(1)
        
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        
        print("✅ Created .env file")
        print("\n⚠️  Please update the .env file with your configuration")
    else:
        print("✅ .env file already exists")

def setup_database():
    """Set up the database"""
    print("\n💾 Setting up database...")
    
    # Run database migrations
    print("🔄 Running database migrations...")
    try:
        run_command("alembic upgrade head")
        print("✅ Database migrations completed successfully")
    except Exception as e:
        print(f"❌ Error running migrations: {str(e)}")
        print("You may need to run: alembic upgrade head")

def main():
    print("\n🚀 Education ERP Server Setup")
    print("=" * 30)
    
    check_dependencies()
    setup_environment()
    setup_database()
    
    print("\n✨ Setup completed successfully!")
    print("\nTo start the server, run:")
    print("  uvicorn main:app --reload")
    print("\nFor production, use a production WSGI server like Gunicorn:")
    print("  gunicorn -k uvicorn.workers.UvicornWorker main:app")

if __name__ == "__main__":
    main()
