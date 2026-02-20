#!/usr/bin/env python3
"""
Тест RAG поиска: проверяем, что можем найти документы по запросу.
"""

from supabase_client import supabase
from embedding import get_embedding
import sys
import math

sys.stdout.reconfigure(encoding='utf-8')

def cosine_similarity(a, b):
    """Вычисляет косинусное сходство между двумя векторами."""
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot_product / (norm_a * norm_b)

def search_documents(query: str, limit: int = 3):
    """Поиск документов по сходству с запросом."""
    
    # Получаем эмбеддинг запроса
    query_embedding = get_embedding(query)
    
    # Получаем все документы с эмбеддингами
    res = supabase.table("documents").select("id, title, doc_type, full_text, embedding").execute()
    
    if not res.data:
        print("❌ Нет документов в базе")
        return []
    
    # Вычисляем сходство
    results = []
    for doc in res.data:
        if doc.get('embedding'):
            similarity = cosine_similarity(query_embedding, doc['embedding'])
            results.append({
                'title': doc['title'],
                'doc_type': doc['doc_type'],
                'full_text': doc['full_text'],
                'similarity': similarity
            })
    
    # Сортируем по сходству
    results.sort(key=lambda x: x['similarity'], reverse=True)
    
    return results[:limit]

# Тестируем
print("🔍 Тест RAG поиска\n")
print("=" * 60)

test_queries = [
    "Как сделать ПЦР?",
    "Техника безопасности",
    "Как выделить ДНК?",
]

for query in test_queries:
    print(f"\n📌 Запрос: {query}")
    print("-" * 60)
    
    results = search_documents(query, limit=2)
    
    for i, doc in enumerate(results, 1):
        print(f"\n  {i}. {doc['title']} [{doc['doc_type']}]")
        print(f"     Сходство: {doc['similarity']:.4f}")
        print(f"     Текст: {doc['full_text'][:100]}...")

print("\n" + "=" * 60)
print("✅ Тест завершён!")
