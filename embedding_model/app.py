from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import torch
from sentence_transformers import SentenceTransformer
from pyvi.ViTokenizer import tokenize
import uvicorn
import json
from transformers import AutoTokenizer, AutoModel
import os
from typing import List


app = FastAPI()


# model_name = "dangvantuan/vietnamese-embedding"
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model = AutoModel.from_pretrained("dangvantuan/vietnamese-document-embedding", trust_remote_code=True)
model = SentenceTransformer('dangvantuan/vietnamese-embedding', trust_remote_code=True)


class TextRequest(BaseModel):
    text: str

class BatchTextRequest(BaseModel):
    batch: List[str]


def get_text_embedding(text: str):
    tokens = tokenize(text)[:500]
    # token_pts = tokenizer(text=texts, padding=True, truncation=True, max_length=500, add_special_tokens=True, return_tensors='pt')


 
    # print(token_pts['input_ids'].max(), token_pts['input_ids'].min())
        # outputs = model(**token_pts)
    outputs = model.encode(text)
    return outputs.tolist()
        # return outputs[0].mean(0).mean(0).detach().cpu().numpy().tolist()

def get_batch_embedding(texts: List[str]):
    # token_pts = tokenizer(text=texts, padding=True, truncation=True, max_length=500, add_special_tokens=True, return_tensors='pt')
    tokens_list = [tokenize(text)[:500] for text in texts]
    outputs = model.encode(tokens_list)
    # return outputs.last_hidden_state.mean(dim=1).detach().cpu().numpy().tolist()
    return outputs.tolist()



@app.post("/embedding")
async def vectorize(request: TextRequest):
    embedding = get_text_embedding(request.text)
    return {"embedding": embedding}


@app.post("/batch_embedding")
async def batch_vectorize(request: BatchTextRequest):
    try:
        batch_embedding = get_batch_embedding(request.batch)
        print(len(batch_embedding))
        return {"batch_embedding": batch_embedding}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# if __name__ == '__main__':
#     with open('/mnt/4TData/duong/Working/misc/rag/data/all.json', 'r') as f:
#         data = json.load(f)
    
#     for d in data:
#         try:
#             print(len(get_text_embedding(f"Trích dẫn ở: {d['title']} \n Nội dung như sau: {d['context']}")))
#         except:
#             print(len(tokenize(f"Trích dẫn ở: {d['title']} \n Nội dung như sau: {d['context']}")))
#             print(model)
#             break
#         # break

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=5000, timeout_keep_alive=60, reload=True)