from fastapi import FastAPI
from src.api import health_router, document_router
import uvicorn

app = FastAPI(    
    title="Indexing",
    docs_url="/idx/docs",  
    redoc_url="/idx/redoc",
    openapi_url="/idx/openapi.json")

# Include routes
app.include_router(health_router.router)
app.include_router(document_router.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=True, timeout_keep_alive=60)