# C:\Lobna\STAGE_WEVIOO\Project\pipeline_orchestration\event_monitoring\event_service_api.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import Dict, Any
from .event_service import CTIEventService, CTIEvent, EventType, Priority
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="CTI Event Service API")

# Dépendance pour la clé API
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)
api_key = os.getenv("EVENT_SERVICE_API_KEY")


async def get_api_key(api_key_param: str = Depends(api_key_header)):
    if api_key_param != api_key:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key_param


# Modèle pour les réponses
class SourceStatus(BaseModel):
    name: str
    status: str
    last_trigger: str | None = None
    cooldown_remaining_minutes: float | None = None
    can_trigger: bool
    metadata: Dict[str, Any] | None = None


# Modèle pour les requêtes de trigger
class TriggerRequest(BaseModel):
    source_name: str
    reason: str | None = "Manual trigger via API"
    priority: str = "normal"


# Modèle pour les réponses de trigger
class TriggerResponse(BaseModel):
    status: str
    message: str
    event_id: str | None = None
    timestamp: str


# Endpoint pour les statuts des sources
@app.get("/api/event-service/sources/status", response_model=Dict[str, SourceStatus])
async def get_sources_status(api_key: str = Depends(get_api_key)):
    event_service = CTIEventService()
    # Simuler les statuts si sources_config est vide
    if not hasattr(
        event_service, "sources_config"
    ) or not event_service.sources_config.get("sources"):
        logger.warning("No sources configured, returning default status.")
        return {
            "default": SourceStatus(name="default", status="ready", can_trigger=True)
        }
    # Retourner les statuts pour chaque source
    statuses = {}
    sources = event_service.sources_config.get("sources", [])

    # Handle both list and dict formats
    if isinstance(sources, list):
        for source in sources:
            if isinstance(source, dict) and "name" in source:
                source_name = source["name"]
                status = event_service.get_source_status(source_name)
                statuses[source_name] = SourceStatus(
                    name=source_name,
                    status=status.get("status", "unknown"),
                    last_trigger=status.get("last_trigger"),
                    cooldown_remaining_minutes=status.get("cooldown_remaining_minutes"),
                    can_trigger=status.get("can_trigger", False),
                    metadata={"description": source.get("description", "")},
                )
    elif isinstance(sources, dict):
        for source_name, config in sources.items():
            status = event_service.get_source_status(source_name)
            statuses[source_name] = SourceStatus(**status)

    return statuses


# Endpoint pour déclencher un événement sur une source
@app.post("/api/event-service/trigger", response_model=TriggerResponse)
async def trigger_source(request: TriggerRequest, api_key: str = Depends(get_api_key)):
    """
    Déclenche un événement manuel sur une source spécifiée.
    Sources disponibles: otx, rss, tuncert, twitter, blog
    """
    try:
        event_service = CTIEventService()

        # Obtenir les sources disponibles dynamiquement
        available_sources = event_service.get_available_sources()
        if not available_sources:
            # Fallback: essayer de lire depuis sources.yaml ou configuration
            if hasattr(
                event_service, "sources_config"
            ) and event_service.sources_config.get("sources"):
                sources = event_service.sources_config["sources"]
                if isinstance(sources, list):
                    available_sources = [
                        s.get("name")
                        for s in sources
                        if isinstance(s, dict) and s.get("name")
                    ]
                elif isinstance(sources, dict):
                    available_sources = list(sources.keys())
            else:
                # Dernière option: sources par défaut
                available_sources = ["otx", "rss", "tuncert", "twitter", "blog"]
                logger.warning("Using default sources list, no configuration found")

        if request.source_name not in available_sources:
            raise HTTPException(
                status_code=400,
                detail=f"Source '{request.source_name}' not available. Available sources: {', '.join(available_sources)}",
            )

        # Créer l'événement
        from datetime import datetime

        event = CTIEvent(
            source_name=request.source_name,
            event_type=EventType.MANUAL_TRIGGER.value,
            timestamp=datetime.utcnow().isoformat(),
            reason=request.reason or "Manual trigger via API",
            priority=Priority.NORMAL if request.priority == "normal" else Priority.HIGH,
        )

        # Déclencher l'événement
        result = event_service.trigger_event(event)

        if result.get("status") == "triggered":
            return TriggerResponse(
                status="triggered",
                message=f"Event successfully triggered for source '{request.source_name}'",
                event_id=result.get("event_id"),
                timestamp=event.timestamp,
            )
        else:
            return TriggerResponse(
                status="failed",
                message=result.get("message", "Unknown error occurred"),
                event_id=None,
                timestamp=event.timestamp,
            )

    except Exception as e:
        logger.error(
            f"Error triggering event for source {request.source_name}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to trigger event: {str(e)}"
        )


# Endpoint pour lister les sources disponibles
@app.get("/api/event-service/sources")
async def get_available_sources(api_key: str = Depends(get_api_key)):
    """
    Retourne la liste des sources disponibles pour le trigger
    """
    try:
        event_service = CTIEventService()

        # Obtenir les sources dynamiquement depuis le service
        available_sources = event_service.get_available_sources()

        if not available_sources:
            # Fallback: lire depuis la configuration
            if hasattr(
                event_service, "sources_config"
            ) and event_service.sources_config.get("sources"):
                sources = event_service.sources_config["sources"]
                if isinstance(sources, list):
                    available_sources = [
                        s.get("name")
                        for s in sources
                        if isinstance(s, dict) and s.get("name")
                    ]
                elif isinstance(sources, dict):
                    available_sources = list(sources.keys())
            else:
                # Dernière option: sources par défaut
                available_sources = ["otx", "rss", "tuncert", "twitter", "blog"]
                logger.warning("Using default sources list, no configuration found")

        return {
            "sources": available_sources,
            "description": "Available CTI event sources for manual triggering",
            "source": (
                "event_service_config"
                if hasattr(event_service, "sources_config")
                else "default"
            ),
        }

    except Exception as e:
        logger.error(f"Error fetching available sources: {str(e)}")
        # Fallback en cas d'erreur
        return {
            "sources": ["otx", "rss", "tuncert", "twitter", "blog"],
            "description": "Default CTI event sources (fallback)",
            "source": "fallback",
            "error": str(e),
        }
