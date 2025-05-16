#!/bin/bash
# Database Setup Helper for WasteWorks
# This script helps set up the PostgreSQL database for local development

# Color codes for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}WasteWorks Database Setup Helper${NC}"
echo "This script will help you set up the PostgreSQL database for local development."
echo

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo -e "${RED}PostgreSQL is not installed or not in your PATH.${NC}"
    echo "Please install PostgreSQL before continuing:"
    echo "  - For Windows: https://www.postgresql.org/download/windows/"
    echo "  - For macOS: brew install postgresql"
    echo "  - For Ubuntu/Debian: sudo apt install postgresql postgresql-contrib"
    exit 1
fi

echo -e "${GREEN}PostgreSQL is installed.${NC}"

# Get database connection details
read -p "Enter database name [wasteworks]: " DB_NAME
DB_NAME=${DB_NAME:-wasteworks}

read -p "Enter database username [postgres]: " DB_USER
DB_USER=${DB_USER:-postgres}

read -sp "Enter database password: " DB_PASS
echo

read -p "Enter database host [localhost]: " DB_HOST
DB_HOST=${DB_HOST:-localhost}

read -p "Enter database port [5432]: " DB_PORT
DB_PORT=${DB_PORT:-5432}

# Create database
echo -e "\n${YELLOW}Creating database...${NC}"
PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "CREATE DATABASE $DB_NAME WITH ENCODING 'UTF8';" postgres

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to create database. Check your credentials and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}Database '$DB_NAME' created successfully!${NC}"

# Generate DATABASE_URL
DB_URL="postgresql://$DB_USER:$DB_PASS@$DB_HOST:$DB_PORT/$DB_NAME"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "\n${YELLOW}Creating .env file...${NC}"
    cp .env_sample .env
    
    # Generate a random SESSION_SECRET
    SESSION_SECRET=$(python -c "import secrets; print(secrets.token_hex(16))")
    
    # Update .env file with actual values
    sed -i.bak "s|DATABASE_URL=.*|DATABASE_URL=$DB_URL|g" .env
    sed -i.bak "s|SESSION_SECRET=.*|SESSION_SECRET=$SESSION_SECRET|g" .env
    rm -f .env.bak
    
    echo -e "${GREEN}.env file created with your database configuration!${NC}"
else
    echo -e "\n${YELLOW}.env file already exists. Updating DATABASE_URL...${NC}"
    sed -i.bak "s|DATABASE_URL=.*|DATABASE_URL=$DB_URL|g" .env
    rm -f .env.bak
    echo -e "${GREEN}.env file updated with your database configuration!${NC}"
fi

echo -e "\n${GREEN}Database setup complete!${NC}"
echo "Your DATABASE_URL is: $DB_URL"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Run 'python recreate_db.py' to initialize your database schema"
echo "2. Run 'python main.py' to start the application"
echo
echo -e "${YELLOW}For deployment to Render.com:${NC}"
echo "1. Create a PostgreSQL database on Render"
echo "2. Use the DATABASE_URL provided by Render"
echo "3. Set the following environment variables in Render:"
echo "   - SESSION_SECRET (a random string)"
echo "   - FLASK_ENV=production"
echo "   - PYTHONUNBUFFERED=true"