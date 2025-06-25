# Education ERP System - Setup Guide

## Prerequisites

- Python 3.11 or higher
- PostgreSQL database
- Redis (optional, for caching and background tasks)

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Edrp-server
   ```

2. **Run the setup script**
   - On Windows: Double-click `setup.bat` or run it from the command line
   - On Linux/Mac: Run `chmod +x setup.sh` then `./setup.sh`

3. **Configure environment variables**
   - Copy `.env.example` to `.env`
   - Update the values in `.env` with your configuration
   - Make sure to set a strong `SECRET_KEY`
   - Update `DATABASE_URL` with your PostgreSQL connection string

4. **Run the application**
   - On Windows: Double-click `run.bat` or run it from the command line
   - On Linux/Mac: Run `chmod +x run.sh` then `./run.sh`

5. **Access the application**
   - API Documentation: http://localhost:8000/docs
   - Interactive API: http://localhost:8000/redoc

## Database Setup

1. Create a new PostgreSQL database
2. Update the `DATABASE_URL` in your `.env` file:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/dbname
   ```
3. Run migrations:
   ```bash
   alembic upgrade head
   ```

## Environment Variables

See `.env.example` for all available configuration options.

## First Run

1. The first time you run the application, you'll need to create an admin user.
2. Use the `/api/auth/register` endpoint with the following payload:
   ```json
   {
     "email": "admin@example.com",
     "password": "your_secure_password",
     "role": "admin"
   }
   ```
3. Then log in using the `/api/auth/login` endpoint to get your access token.

## Development

- Run tests: `pytest`
- Run with hot-reload: `uvicorn main:app --reload`
- Access API docs: http://localhost:8000/docs

## Deployment

For production deployment, make sure to:
1. Set `ENVIRONMENT=production` in your `.env`
2. Use a proper WSGI server like Gunicorn:
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
   ```
3. Set up a reverse proxy (Nginx/Apache) in front of your application
4. Set up SSL/TLS for secure connections
