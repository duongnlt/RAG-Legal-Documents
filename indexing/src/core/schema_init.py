from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams



def init_qdrant_schema(client: QdrantClient, collection_name: str):
    if collection_name in client.get_collections().collections:
        client.delete_collection(collection_name)

    existing_collections = [col.name for col in client.get_collections().collections]
    if collection_name in existing_collections:
        print(f"Collection '{collection_name}' already exists.")
    else:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)
        )