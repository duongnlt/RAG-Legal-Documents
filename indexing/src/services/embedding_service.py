import requests
from fastapi import HTTPException
from src.utils.config import Config
from typing import List
from src.utils.logger import get_logger

logger = get_logger(__name__)
class EmbeddingService:
    @staticmethod
    def embed_document(texts: List[str]) -> List[List[float]]:
        try:
            response = requests.post(
                Config.VECTORIZE_URL, 
                json={"batch": texts}
            )
            logger.info("Send succesfully!")
            logger.info(response.json().get("batch_embedding"))
            response.raise_for_status()  # Raises HTTPError for bad responses
            return response.json().get("batch_embedding")
        except requests.exceptions.ConnectionError as e:
            raise HTTPException(
                status_code=502, detail=f"Unable to connect to vectorization service: {str(e)}"
            )
        except requests.exceptions.Timeout as e:
            raise HTTPException(
                status_code=504, detail=f"Vectorization service timed out: {str(e)}"
            )
        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=500, detail=f"Error in vectorization service: {str(e)}"
            )