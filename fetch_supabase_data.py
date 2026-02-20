#!/usr/bin/env python3
"""
Получение данных из Supabase для использования в приложении.
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

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 60)
print("FETCHING DATA FROM SUPABASE")
print("=" * 60)

# Get all documents
print("\n[DOCUMENTS]")
result = supabase.table("documents").select("*").execute()
docs = result.data if result.data else []
print(f"Total: {len(docs)} documents")

for doc in docs:
    print(f"\n  ID: {doc['id']}")
    print(f"  Title: {doc['title']}")
    print(f"  Type: {doc['doc_type']}")
    text_preview = doc['full_text'][:100].replace('\n', ' ') if doc.get('full_text') else 'N/A'
    print(f"  Text preview: {text_preview}...")
    print(f"  Has embedding: {'Yes' if doc.get('embedding') else 'No'}")

# Get all chunks
print("\n\n[DOCUMENT CHUNKS]")
result = supabase.table("document_chunks").select("*").execute()
chunks = result.data if result.data else []
print(f"Total: {len(chunks)} chunks")

for chunk in chunks:
    print(f"\n  ID: {chunk['id']}")
    print(f"  Document ID: {chunk['document_id']}")
    content_preview = chunk.get('content', chunk.get('chunk_text', 'N/A'))[:100].replace('\n', ' ')
    print(f"  Content: {content_preview}...")
    print(f"  Token count: {chunk.get('token_count', 'N/A')}")
    print(f"  Has embedding: {'Yes' if chunk.get('embedding') else 'No'}")

print("\n" + "=" * 60)
