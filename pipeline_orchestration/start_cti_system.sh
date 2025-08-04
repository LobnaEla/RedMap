# Start the complete CTI system

set -e

echo "🚀 Starting CTI Event-Driven System..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration and run again."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p config
mkdir -p event_monitoring/logs
mkdir -p airflow/dags
mkdir -p airflow/logs
mkdir -p airflow/plugins
mkdir -p monitoring

# Build and start services
echo "🏗️  Building and starting services..."
docker-compose up -d --build

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
docker-compose ps

# Show logs for event service
echo "📋 Event Service Status:"
docker-compose logs --tail=20 cti-event-service

echo "✅ CTI System Started Successfully!"
echo ""
echo "🌐 Access URLs:"
echo "   n8n:              http://localhost:5678 (admin/admin123)"
echo "   Airflow:          http://localhost:8080 (airflow/airflow)"
echo ""
echo "📊 Monitor logs:"
echo "   docker-compose logs -f cti-event-service"
echo ""
echo "🛑 Stop system:"
echo "   docker-compose down"

# Optional: Show real-time logs
read -p "Show real-time event service logs? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose logs -f cti-event-service
fi