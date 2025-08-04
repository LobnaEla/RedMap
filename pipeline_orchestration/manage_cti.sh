# Management script for CTI system

show_help() {
    echo "CTI Event-Driven System Management"
    echo ""
    echo "Usage: ./manage_cti.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start         Start the complete CTI system"
    echo "  stop          Stop all services"
    echo "  restart       Restart all services"
    echo "  status        Show service status"
    echo "  logs          Show event service logs"
    echo "  logs-all      Show all service logs"
    echo "  shell         Access event service shell"
    echo "  redis         Access Redis CLI"
    echo "  trigger       Manually trigger a source"
    echo "  monitor       Show monitoring dashboard"
    echo "  cleanup       Clean up volumes and containers"
    echo "  help          Show this help message"
}

start_system() {
    echo "🚀 Starting CTI Event-Driven System..."
    docker-compose up -d --build
    sleep 5
    docker-compose ps
    echo "✅ System started!"
}

stop_system() {
    echo "🛑 Stopping CTI System..."
    docker-compose down
    echo "✅ System stopped!"
}

restart_system() {
    echo "🔄 Restarting CTI System..."
    docker-compose restart
    sleep 5
    docker-compose ps
    echo "✅ System restarted!"
}

show_status() {
    echo "📊 CTI System Status:"
    docker-compose ps
    echo ""
    echo "🔍 Service Health:"
    docker-compose exec cti-event-service python -c "
from event_service import CTIEventService
import json
service = CTIEventService()
status = service.get_all_sources_status()
print(json.dumps(status, indent=2))
" 2>/dev/null || echo "Event service not ready"
}

show_logs() {
    docker-compose logs -f cti-event-service
}

show_all_logs() {
    docker-compose logs -f
}

access_shell() {
    echo "🐚 Accessing event service shell..."
    docker-compose exec cti-event-service /bin/bash
}

access_redis() {
    echo "🔴 Accessing Redis CLI..."
    docker-compose exec redis redis-cli
}

trigger_source() {
    echo "Available sources: otx, rss, tuncert, twitter, blog"
    read -p "Enter source name: " source
    read -p "Enter reason (optional): " reason
    
    if [ -z "$reason" ]; then
        reason="Manual trigger via management script"
    fi
    
    docker-compose exec cti-event-service python -c "
from event_service import CTIEventService
import json
service = CTIEventService()
result = service.trigger_source('$source', reason='$reason')
print(json.dumps(result, indent=2))
"
}

show_monitoring() {
    echo "📈 Opening..."
    echo "n8n: http://localhost:5678 (admin/admin123)"
    echo "Airflow: http://localhost:8080 (airflow/airflow)"
}

cleanup_system() {
    read -p "⚠️  This will remove all containers and volumes. Continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🧹 Cleaning up..."
        docker-compose down -v --remove-orphans
        docker system prune -f
        echo "✅ Cleanup complete!"
    else
        echo "❌ Cleanup cancelled"
    fi
}

# Main command handling
case "${1:-help}" in
    start)
        start_system
        ;;
    stop)
        stop_system
        ;;
    restart)
        restart_system
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    logs-all)
        show_all_logs
        ;;
    shell)
        access_shell
        ;;
    redis)
        access_redis
        ;;
    trigger)
        trigger_source
        ;;
    monitor)
        show_monitoring
        ;;
    cleanup)
        cleanup_system
        ;;
    help|*)
        show_help
        ;;
esac