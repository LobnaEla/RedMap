#!/bin/bash

# This script initializes and starts Apache Airflow

set -e

echo "Starting Apache Airflow 2.11 for CTI Pipeline..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running. Please start Docker first."
    exit 1
fi

# Navigate to airflow directory (parent of scripts)
cd "$(dirname "$0")/.."

# Set environment variables if not already set
if ! grep -q "AIRFLOW_UID" .env; then
    echo "Setting AIRFLOW_UID..."
    echo "AIRFLOW_UID=$(id -u)" >> .env
fi

echo "Checking if Airflow is initialized..."

# Check if database is initialized
if ! docker compose ps | grep -q postgres; then
    echo "Initializing Airflow database..."
    docker compose up airflow-init
fi

echo "Starting Airflow services..."

# Start all services
docker compose up -d

echo "Waiting for services to be healthy..."

# Wait for services to be ready
sleep 10

echo "Checking service status..."
docker compose ps

echo ""
echo "Airflow 2.11 is now running!"
echo ""
echo "Web UI: http://localhost:8080"
echo ""
echo "Test DAG 'test_dag' should be visible in the UI"
echo ""
echo "To stop: docker compose down"
echo "To view logs: docker compose logs [service-name]"
echo ""
