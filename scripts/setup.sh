#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Education ERP Setup 🚀${NC}"
echo -e "${YELLOW}This script will help you set up your development environment.${NC}"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env file${NC}"
    echo -e "${YELLOW}Please edit the .env file with your configuration.${NC}"
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Python is installed${NC}"
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip3 is not installed. Please install pip.${NC}"
    exit 1
else
    echo -e "${GREEN}✅ pip is installed${NC}"
fi

# Install Python dependencies
echo -e "\n${YELLOW}Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}⚠️  PostgreSQL is not installed. Please install PostgreSQL.${NC}"
    echo -e "  On Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib"
    echo -e "  On macOS: brew install postgresql"
    echo -e "  On Windows: https://www.postgresql.org/download/windows/"
else
    echo -e "${GREEN}✅ PostgreSQL is installed${NC}"
fi

# Check if Redis is installed
if ! command -v redis-cli &> /dev/null; then
    echo -e "${YELLOW}⚠️  Redis is not installed. Please install Redis.${NC}"
    echo -e "  On Ubuntu/Debian: sudo apt-get install redis-server"
    echo -e "  On macOS: brew install redis"
    echo -e "  On Windows: https://github.com/tporadowski/redis/releases"
else
    echo -e "${GREEN}✅ Redis is installed${NC}"
fi

# Run database migrations
echo -e "\n${YELLOW}Running database migrations...${NC}"
alembic upgrade head

# Create uploads directory if it doesn't exist
mkdir -p uploads

echo -e "\n${GREEN}✨ Setup completed successfully! ✨${NC}"
echo -e "\nTo start the development server, run:"
echo -e "  ${YELLOW}uvicorn main:app --reload${NC}"
echo -e "\nThen open your browser to:"
echo -e "  http://localhost:8000${NC}"
echo -e "\nFor API documentation:"
echo -e "  http://localhost:8000/docs${NC}"
