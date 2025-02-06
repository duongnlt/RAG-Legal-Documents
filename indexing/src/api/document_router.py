from fastapi import APIRouter, HTTPException, File, UploadFile
import json
from qdrant_client import QdrantClient
from src.services.document_service import DocumentService
from src.core.schema_init import init_qdrant_schema
from src.utils.logger import get_logger
from src.utils.config import Config
logger = get_logger(__name__)
router = APIRouter()

@router.post("/embed_and_import_json")
async def embed_and_import_json(file: UploadFile = File(...)):
    try:
        json_data = json.load(file.file)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    
    client = QdrantClient(Config.QDRANT_URL)
    service = DocumentService(client)
    
    init_qdrant_schema(client, Config.COLLECTION_NAME)
    service.process_and_import_documents(json_data)
    
    return {"message": "All documents successfully imported into Qdrant"}