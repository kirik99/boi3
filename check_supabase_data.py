#!/usr/bin/env python3
"""
Проверка: есть ли данные в Supabase.
"""

from supabase_client import supabase
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("📦 Проверка данных в Supabase\n")
print("=" * 60)

# Получаем все документы
res = supabase.table("documents").select("*").execute()

if not res.data:
    print("❌ База пуста!")
else:
    print(f"✅ Найдено документов: {len(res.data)}\n")
    
    for i, doc in enumerate(res.data, 1):
        print(f"{i}. {doc['title']}")
        print(f"   Тип: {doc['doc_type']}")
        print(f"   Текст: {doc['full_text'][:80]}...")
        has_embedding = 'embedding' in doc and doc['embedding'] is not None
        print(f"   Эмбеддинг: {'✅' if has_embedding else '❌'}")
        print()

print("=" * 60)
