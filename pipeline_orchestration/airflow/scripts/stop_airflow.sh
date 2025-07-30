#!/bin/bash

# This script stops Apache Airflow services

set -e

echo "Stopping Apache Airflow 2.11..."

# Navigate to airflow directory (parent of scripts)
cd "$(dirname "$0")/.."

# Stop all services
docker compose down

echo ""
echo "Airflow services stopped successfully!"
echo ""
echo "To completely remove volumes and data:"
echo "   docker compose down -v"
echo ""
echo "To restart: ./scripts/start_airflow.sh"
echo ""
