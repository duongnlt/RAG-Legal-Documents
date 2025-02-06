from typing import Literal
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from src.utils.config import Config
from src.utils.logger import get_logger
# Not authentication or authorization required to get the health status.
router = APIRouter()

logger = get_logger(__name__)

class HealthResponse(BaseModel):
    status: Literal["ok"] = Field(default="ok")


@router.get("/healthz", tags=["Health"])
async def health() -> HealthResponse:
    """Return ok if the system is up."""
    return HealthResponse(status="ok")


@router.get("/readyz")
async def readiness_check():
    try:
        logger.info("Initializing QdrantClient...")
        client = QdrantClient(Config.QDRANT_URL)
        
        logger.info("Fetching collections from Qdrant...")
        client.get_collections()
        
        logger.info("Making request to VECTORIZE_URL...")
        requests.get(Config.VECTORIZE_URL)
        
        logger.info("All checks passed.")
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="Service not ready")