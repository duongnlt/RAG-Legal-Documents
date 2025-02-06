import asyncio
from src.services.embedding_service import EmbeddingService
from src.utils.logger import get_logger
from src.utils.config import Config
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Batch

logger = get_logger(__name__)

class DocumentService:
    def __init__(self, client: QdrantClient):
        self.client = client

    def process_and_import_documents(self, json_data):
        processed_documents = [
            f"Trích dẫn ở: {item['title']} \n Nội dung như sau: {item['context']}" for item in json_data
        ]

        # vectors = []
        # for idx, document in enumerate(processed_documents):
        #     logger.info(f"Vectorizing document {idx + 1}/{len(processed_documents)}")
        #     vector = EmbeddingService.embed_document(document)
        #     vectors.append(vector)
 
        vectors = EmbeddingService.embed_document(processed_documents)
        logger.info(f"Number of vectors: {len(vectors)}")

        existing_count = self.client.count(collection_name=Config.COLLECTION_NAME)
        logger.info(f"Existing vectors count before upsert: {existing_count}")

        if not vectors:
            logger.error("Vector list is empty!")
        elif not isinstance(vectors, list) or not all(isinstance(v, list) for v in vectors):
            logger.error("Vectors should be a list of lists.")
        elif not all(len(v) == 768 for v in vectors):  # Ensure correct embedding size
            logger.error("One or more vectors have an incorrect dimension!")
        else:
            logger.info("All vectors are valid, proceeding with upsert.")

        response = self.client.upsert(collection_name=Config.COLLECTION_NAME, points=Batch(
            ids=[idx + 1 for idx in range(len(vectors))],
            payloads=[{"content": document} for document in processed_documents],
            vectors=vectors
        ))


        logger.info(f"Upsert response: {response}")
        new_count = self.client.count(collection_name=Config.COLLECTION_NAME)
        logger.info(f"New vectors count after upsert: {new_count}")
        
        logger.info("All documents successfully imported into Qdrant")