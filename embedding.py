from sentence_transformers import SentenceTransformer

# Локальная модель для эмбеддингов
_model = None

def get_model() -> SentenceTransformer:
    """Ленивая загрузка модели."""
    global _model
    if _model is None:
        print("Loading model: all-MiniLM-L6-v2...")
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def get_embedding(text: str) -> list[float]:
    """Получить эмбеддинг текста локально."""
    model = get_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()

def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Получить эмбеддинги для списка текстов."""
    model = get_model()
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings.tolist()
