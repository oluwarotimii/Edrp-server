# Education ERP System - Docker Setup

This project uses Docker to containerize the application and PostgreSQL database for easy deployment.

## Prerequisites

- Docker Engine (https://docs.docker.com/engine/install/)
- Docker Compose (usually included with Docker Desktop)

## Quick Start

1. Make sure Docker is running on your system

2. Navigate to the project directory:
   ```bash
   cd /path/to/your/edrp
   ```

3. Build and start the services:
   ```bash
   docker-compose up --build
   ```

4. The application will be available at:
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Docker Services

This setup includes two services:

1. **Database (PostgreSQL)**:
   - Image: postgres:16
   - Database: edrp
   - User: edrp
   - Password: edrp2025
   - Port: 5432 (internal), mapped to 5432 on host

2. **Application**:
   - Built from the project Dockerfile
   - Port: 8000 (internal), mapped to 8000 on host
   - Automatically runs database migrations on startup

## Development Commands

### Build and run in detached mode:
```bash
docker-compose up --build -d
```

### View logs:
```bash
docker-compose logs -f
```

### Run commands in the app container:
```bash
docker-compose exec app bash
```

### Stop services:
```bash
docker-compose down
```

### Stop and remove volumes (removes database):
```bash
docker-compose down -v
```

## Production Deployment

For production deployment on cloud platforms:

### Digital Ocean:
1. Create a Droplet with Docker pre-installed
2. Clone your repository
3. Run: `docker-compose up --build -d`

### AWS (EC2):
1. Launch an EC2 instance with Docker
2. Clone your repository
3. Run: `docker-compose up --build -d`

### Azure:
1. Create a Virtual Machine with Docker
2. Clone your repository
3. Run: `docker-compose up --build -d`

## Notes

- The database data is persisted using a Docker volume named `postgres_data`
- File uploads are stored in the `./uploads` directory on the host
- The application automatically runs Alembic migrations when starting
- Environment variables are configured in the docker-compose.yml file
- The .dockerignore file ensures only necessary files are copied to the container
