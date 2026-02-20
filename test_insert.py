from supabase_client import supabase
import sys

# вставляем тестовый документ
res = supabase.table("documents").insert({
    "title": "Тестовая методика",
    "doc_type": "method",
    "full_text": "Это первая тестовая запись лаборатории"
}).execute()

# Выводим результат в кодировке UTF-8
sys.stdout.reconfigure(encoding='utf-8')
print(f"Data: {res.data}")
print(f"Count: {res.count}")
