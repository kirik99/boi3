import requests
import os
from dotenv import load_dotenv

# Загружаем основные переменные и секреты
load_dotenv()
load_dotenv(".env.secrets")

HF_TOKEN = os.getenv("HF_TOKEN")

# Модель для эмбеддингов через HF Inference API
HF_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

def get_embedding(text: str) -> list[float]:
    """Получить эмбеддинг текста через Hugging Face Inference API."""
    
    url = f"https://router.huggingface.co/hf-inference/models/{HF_EMBEDDING_MODEL}"
    
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "inputs": text
    }
    
    res = requests.post(url, headers=headers, json=data)
    res.raise_for_status()
    
    return res.json()

def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Получить эмбеддинги для списка текстов."""
    return [get_embedding(text) for text in texts]
