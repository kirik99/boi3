#!/usr/bin/env python3
"""
Проверка подключения к Supabase и получение данных.
"""
import os
import sys

# Setup UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

print("=" * 60)
print("DB & ML CONNECTION CHECK")
print("=" * 60)

print("\n[CONFIG] Configuration:")
print(f"  SUPABASE_URL: {SUPABASE_URL}")
print(f"  SUPABASE_KEY: {SUPABASE_KEY[:20]}...")
print(f"  DATABASE_URL: {DATABASE_URL[:50]}...")
hf_token = os.getenv('HF_TOKEN')
print(f"  HF_TOKEN: {hf_token[:20] if hf_token else 'Not set'}...")

# Check Supabase
print("\n[SUPABASE] Checking Supabase...")
try:
    from supabase import create_client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Get tables
    print("  [OK] Supabase client created")
    
    # Check document_chunks table
    try:
        data, count = supabase.table("document_chunks").select("*", count="exact").limit(5).execute()
        print(f"  [OK] document_chunks: {count} records")
        if data.data:
            print(f"    Sample: {data.data[0].get('title', 'N/A')[:50]}")
    except Exception as e:
        print(f"  [WARN] document_chunks: {e}")
    
    # Check documents table
    try:
        data, count = supabase.table("documents").select("*", count="exact").limit(5).execute()
        print(f"  [OK] documents: {count} records")
    except Exception as e:
        print(f"  [WARN] documents: {e}")
        
except ImportError:
    print("  [ERROR] Supabase library not installed: pip install supabase")
except Exception as e:
    print(f"  [ERROR] Connection error: {e}")

# Check ML/embedding
print("\n[ML] Checking ML (embeddings)...")
try:
    from embedding import get_embedding
    print("  [OK] Embedding module loaded")
    
    test_text = "Hello, this is a test query"
    print(f"  -> Generating embedding for: '{test_text}'")
    
    embedding = get_embedding(test_text)
    print(f"  [OK] Embedding generated: {len(embedding)} dimensions")
    print(f"    First 5 values: {embedding[:5]}")
    
except ImportError as e:
    print(f"  [ERROR] Import error: {e}")
    print("    Install dependencies: pip install -r requirements.txt")
except Exception as e:
    print(f"  [ERROR] Embedding generation error: {e}")

# Check embedding server
print("\n[SERVER] Checking embedding server (port 8000)...")
try:
    import requests
    response = requests.post(
        "http://localhost:8000/embed",
        json={"text": "test"},
        timeout=5
    )
    if response.ok:
        data = response.json()
        print(f"  [OK] Embedding server responds: {len(data.get('embedding', []))} dimensions")
    else:
        print(f"  [WARN] Embedding server error: {response.status_code}")
except requests.exceptions.ConnectionError:
    print("  [WARN] Embedding server not running on port 8000")
    print("    Start with: python embedding_server.py")
except Exception as e:
    print(f"  [WARN] Error: {e}")

print("\n" + "=" * 60)
print("CHECK COMPLETE")
print("=" * 60)
