#!/usr/bin/env python3
"""
Добавляет эмбеддинги к существующим документам в Supabase.
Использует локальную модель sentence-transformers.
"""

from supabase_client import supabase
from embedding import get_embedding
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("🔄 Добавление эмбеддингов к документам\n")
print("=" * 60)

# Получаем все документы
res = supabase.table("documents").select("id, title, full_text").execute()

if not res.data:
    print("❌ Нет документов в базе")
    sys.exit(1)

docs = res.data
print(f"Найдено документов: {len(docs)}\n")

updated = 0
failed = 0

for doc in docs:
    try:
        # Получаем эмбеддинг
        embedding = get_embedding(doc['full_text'])
        
        # Обновляем документ
        update_res = supabase.table("documents").update({
            "embedding": embedding
        }).eq("id", doc['id']).execute()
        
        print(f"✓ {doc['title']}")
        updated += 1
        
    except Exception as e:
        print(f"✗ {doc['title']}: {e}")
        failed += 1

print("\n" + "=" * 60)
print(f"✅ Обновлено: {updated}")
print(f"❌ Ошибок: {failed}")

if updated == len(docs):
    print("\n🎉 Все документы обновлены!")
