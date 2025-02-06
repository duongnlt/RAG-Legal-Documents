import os

class Config:
    QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
    VECTORIZE_URL = os.getenv("VECTORIZE_URL", "http://emb-svc.emb.svc.cluster.local:81/embedding")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "documents")
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", 8005))