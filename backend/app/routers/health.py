import datetime
from fastapi import APIRouter, status
from app.core.config import settings
from app.database.database import check_db_connection
from app.schemas.verification import HealthCheckResponse, HealthCheckDatabase
from app.services.blockchain_service import blockchain_service

router = APIRouter(prefix="/health", tags=["Health & Status"])

@router.get("", status_code=status.HTTP_200_OK, response_model=HealthCheckResponse)
def get_health_status():
    """
    Health check endpoint verifying application gateway status and database connectivity.
    Returns HTTP 200 when system is operational.
    """
    db_info = check_db_connection()
    
    db_schema = HealthCheckDatabase(
        connected=db_info.get("connected", False),
        dialect=db_info.get("dialect", "unknown"),
        url=db_info.get("url")
    )
    
    return HealthCheckResponse(
        status="healthy" if db_info.get("connected") else "unhealthy",
        version=settings.VERSION,
        database=db_schema,
        timestamp=datetime.datetime.utcnow().isoformat() + "Z"
    )

@router.get("/blockchain", status_code=status.HTTP_200_OK)
def get_blockchain_health():
    """
    Blockchain Health Check Endpoint.
    Verifies RPC reachability, Chain ID, Latest block number, Contract address, and Contract accessibility.
    """
    health_data = blockchain_service.health_check()
    return {
        "status": health_data.get("status", "UNHEALTHY"),
        "blockchain": health_data,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }
