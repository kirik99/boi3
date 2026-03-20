import os
import time
import sqlite3
import json
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

# Setup reliable SQLite cache for embeddings
emb_cache_conn = sqlite3.connect('embedding_cache.db', check_same_thread=False)
emb_cache_conn.execute('CREATE TABLE IF NOT EXISTS emb_cache (text TEXT PRIMARY KEY, embedding TEXT)')
emb_cache_conn.commit()

HF_TOKEN = os.getenv("HF_TOKEN")
hf_client = InferenceClient(token=HF_TOKEN) if HF_TOKEN else None
# Use the same model as the uploaders to maintain 1024 dimensions
MODEL_ID = "intfloat/multilingual-e5-large"

def get_embedding(text: str) -> list[float]:
    """Получить эмбеддинг текста через Hugging Face API с локальным кэшированием."""
    # Check cache first for exact match embedding
    cached = emb_cache_conn.execute('SELECT embedding FROM emb_cache WHERE text = ?', (text,)).fetchone()
    if cached:
        return json.loads(cached[0])

    if not hf_client:
        raise ValueError("HF_TOKEN is not set in environment variables")
        
    try:
        embedding = hf_client.feature_extraction(f"passage: {text}", model=MODEL_ID)
        # feature_extraction might return different nested structures
        if hasattr(embedding, "tolist"):
            embedding = embedding.tolist()
        if isinstance(embedding, list) and len(embedding) > 0 and isinstance(embedding[0], list):
            embedding = embedding[0]
            
        # Save to cache
        emb_cache_conn.execute('INSERT OR REPLACE INTO emb_cache (text, embedding) VALUES (?, ?)', (text, json.dumps(embedding)))
        emb_cache_conn.commit()
        return embedding
    except Exception as e:
        err_msg = str(e).lower()
        if "503" in err_msg or "loading" in err_msg or "10060" in err_msg or "timeout" in err_msg or "rate limit" in err_msg or "429" in err_msg:
            print(f"  API limit or connection issue ({e}). Waiting 20s and retrying...")
            time.sleep(20)
            return get_embedding(text)
        raise e

def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Получить эмбеддинги для списка текстов через Hugging Face API."""
    return [get_embedding(t) for t in texts]
