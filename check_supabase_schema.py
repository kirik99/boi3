#!/usr/bin/env python3
"""
Проверка схем и таблиц в Supabase.
"""
import os
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("=" * 60)
print("SUPABASE SCHEMA INSPECTION")
print("=" * 60)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Get all tables using RPC
print("\n[INFO] Getting tables from public schema...")

# Try to get document_chunks
print("\n[TABLE] document_chunks:")
try:
    result = supabase.table("document_chunks").select("*").limit(3).execute()
    data = result.data
    print(f"  Records: {len(data) if data else 0}")
    if data:
        print(f"  Columns: {list(data[0].keys())}")
        print(f"  Sample:")
        for row in data[:2]:
            title = row.get('title', row.get('chunk_text', 'N/A'))
            print(f"    - {str(title)[:60]}")
except Exception as e:
    print(f"  [ERROR] {e}")

# Try to get documents
print("\n[TABLE] documents:")
try:
    result = supabase.table("documents").select("*").limit(3).execute()
    data = result.data
    print(f"  Records: {len(data) if data else 0}")
    if data:
        print(f"  Columns: {list(data[0].keys())}")
        print(f"  Sample:")
        for row in data[:2]:
            print(f"    - {row.get('title', 'N/A')[:60]}")
except Exception as e:
    print(f"  [ERROR] {e}")

# Try to get conversations
print("\n[TABLE] conversations:")
try:
    data, count = supabase.table("conversations").select("*", count="exact").limit(3).execute()
    print(f"  Records: {count}")
    if data.data:
        print(f"  Columns: {list(data.data[0].keys())}")
except Exception as e:
    print(f"  [ERROR] {e}")

# Try to get messages
print("\n[TABLE] messages:")
try:
    data, count = supabase.table("messages").select("*", count="exact").limit(3).execute()
    print(f"  Records: {count}")
    if data.data:
        print(f"  Columns: {list(data.data[0].keys())}")
except Exception as e:
    print(f"  [ERROR] {e}")

# Check for vector extension
print("\n[EXTENSION] Checking pgvector...")
try:
    # Try to call match_chunks RPC (correct name from hint)
    result = supabase.rpc("match_chunks", {
        "query_embedding": [0.0] * 384,
        "match_limit": 1
    }).execute()
    print("  [OK] RPC match_chunks exists")
except Exception as e:
    print(f"  [INFO] RPC error: {e}")

print("\n" + "=" * 60)
