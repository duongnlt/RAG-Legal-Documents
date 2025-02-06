FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# COPY ./src .
COPY app.py .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8005

ENV QDRANT_URL=http://qdrant.qrant.svc.cluster.local:6333
ENV VECTORIZE_URL=http://emb-svc.emb.svc.cluster.local:81/embedding
ENV MAX_NEW_TOKENS=30
ENV LLM_API_URL=https://1b27-202-191-58-161.ngrok-free.app/generate
ENV TEMPERATURE=0.5



CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8005", "--timeout-keep-alive", "100"]