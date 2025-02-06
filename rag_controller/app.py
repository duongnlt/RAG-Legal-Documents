from fastapi import FastAPI, HTTPException
import qdrant_client
import os
from llama_index.core import PromptTemplate
import asyncio
import qdrant_client.http
import requests
import uvicorn
import logging

QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant.qdrant.svc.cluster.local:6333")
VECTORIZE_URL = os.getenv("VECTORIZE_URL", "http://emb-svc.emb.svc.cluster.local:81/embedding")
LLM_API_URL = os.getenv("LLM_API_URL", "https://50e7-202-191-58-161.ngrok-free.app/generate")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "documents")

MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", 30))
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.5))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING) 


app = FastAPI(
    title="Rag",
    docs_url="/rag/docs",
    redoc_url="/rag/redoc",
    openapi_url="/rag/openapi.json")


@app.get("/healthz")
async def health_check():
    return {"status": "ok"}

@app.post("/query")
async def query(query_str: str):
    db_client = qdrant_client.QdrantClient(url=QDRANT_URL)
    text_data = {"text": query_str}
    try:
        vec_respond = await asyncio.to_thread(requests.post, VECTORIZE_URL, json = text_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Unable to vectorize query: {str(e)}')
    
    if vec_respond.status_code == 200:
        vec = vec_respond.json().get("embedding")
    else:
        print("Failed to get vector, status code:", vec_respond.status_code)
        return None
    
    try:
        db_respond = db_client.query_points(
            collection_name=COLLECTION_NAME,
            query=vec,
            limit=3
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Unable to do similarity search: {str(e)}')
    
    context_str = []
    for point in db_respond.points:
        # logger.warning(f"Content similarity: {doc['_additional']['certainty']}: {document['content']}")
        context_str.append("{:.4f}: {}".format(point.score, point.payload['content']))
    
    context_str = "\n".join(context_str)

    template = (
        "We have provided context information below. \n"
        "---------------------\n"
        "{context_str}"
        "\n---------------------\n"
        "Given this information, please answer the question: {query_str}\n"
    )
    chat_template = PromptTemplate(template)
    messages = chat_template.format_messages(context_str=context_str, query_str=query_str)
    prompt = messages[0].content

    response = await asyncio.to_thread(requests.post, 
        LLM_API_URL,
        json={
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": MAX_NEW_TOKENS,
                "temperature": TEMPERATURE
            }
        },
        verify=False  # Disable SSL certificate verification
    )

    if response.status_code == 200:
        response_json = response.json()
        logger.warning(f"Answer from LLM: {response_json}")
        return response_json
    else:
        print("Failed to get response from LLM, status code:", response.status_code)
        logger.warning(f"Error: {response_json}")
        raise HTTPException(status_code=500, detail="Failed to process the query")
        # return None
    


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8005, reload=True)