# file: app/api/v1/monitor_routes.py

from fastapi import APIRouter, HTTPException
from app.services.kafka_monitoring_service import KafkaMonitoringService

router = APIRouter()

@router.get("/consumer-group-lag", tags=["Monitoring"])
def consumer_group_lag(group_id: str, topic: str, bootstrap_servers: str = "localhost:9092"):
    """
    Get consumer group lag information for the given group and topic.
    """
    try:
        service = KafkaMonitoringService(bootstrap_servers)
        result = service.get_consumer_group_lag(group_id, topic)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))