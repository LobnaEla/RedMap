#!/bin/bash

# This script clears the Airflow cache, DAG history, and log files
set -e

echo "Starting Airflow cache cleanup..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running from airflow directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from the airflow directory containing docker-compose.yml"
    exit 1
fi

# Check for sudo privileges 
print_status "Checking for sudo privileges..."
if ! sudo -n true 2>/dev/null; then
    print_warning "This script requires sudo privileges for Docker operations."
    print_status "Please enter your password when prompted:"
    sudo -v || {
        print_error "Failed to obtain sudo privileges. Exiting."
        exit 1
    }
fi

print_warning "This will clear all Airflow cache, logs, and DAG history. Continue? (y/N)"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    print_status "Operation cancelled."
    exit 0
fi

# Stop all Airflow services
print_status "Stopping Airflow services..."
sudo docker compose down

# Clear db
print_status "Clearing Airflow database..."
sudo docker volume rm airflow_postgres-db-volume 2>/dev/null || print_warning "Postgres volume not found or already removed"

# Clear pip cache
print_status "Clearing pip cache..."
sudo docker volume rm airflow_pip-cache-volume 2>/dev/null || print_warning "Pip cache volume not found or already removed"

# Clear local log files
print_status "Clearing local log files..."
if [ -d "logs" ]; then
    sudo rm -rf logs/*
    print_status "Local logs cleared"
else
    print_warning "Logs directory not found"
fi

# Clear DAG processor cache files
print_status "Clearing DAG cache files..."
find dags/ -name "*.pyc" -delete 2>/dev/null || true
find dags/ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
print_status "Python cache files cleared"

# Clear any SQLite database files (if they exist)
print_status "Clearing any local database files..."
sudo rm -f airflow.db airflow.cfg.bak *.pid 2>/dev/null || true



print_status "Cache cleanup completed!"
print_warning "Note: All DAG runs, task instances, and logs have been cleared."
