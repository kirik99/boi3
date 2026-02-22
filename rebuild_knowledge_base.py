import os
import requests
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
EMBEDDING_SERVER_URL = "http://localhost:8000/embed"

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ SUPABASE_URL or SUPABASE_KEY not found in .env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_embedding(text):
    try:
        r = requests.post(EMBEDDING_SERVER_URL, json={"text": text})
        r.raise_for_status()
        return r.json()["embedding"]
    except Exception as e:
        print(f"❌ Failed to get embedding for: {text[:50]}... Error: {e}")
        return None

def rebuild():
    print("🚀 Rebuilding Knowledge Base...")

    # 1. Fetch all documents
    print("📥 Fetching documents from Supabase...")
    docs_res = supabase.table("documents").select("*").execute()
    documents = docs_res.data

    if not documents:
        print("⚠ No documents found in 'documents' table.")
        return

    print(f"Found {len(documents)} documents.")

    # 2. Clear old chunks
    print("🗑 Clearing old chunks from 'document_chunks'...")
    # Use a filter that matches all rows and is type-safe (content is always text)
    supabase.table("document_chunks").delete().neq("content", "____non_existent_string____").execute() 

    # 3. Process each document
    new_chunks = []
    for doc in documents:
        doc_id = doc["id"]
        title = doc.get("title", "Untitled")
        content = doc.get("full_text") or doc.get("content") or ""

        if not content:
            print(f"⏩ Skipping empty document: {title}")
            continue

        print(f"📄 Processing: {title} ({len(content)} chars)")

        # Simple chunking by paragraph/size
        chunks = [content[i:i+1000] for i in range(0, len(content), 800)]
        
        for chunk_text in chunks:
            embedding = get_embedding(chunk_text)
            if embedding:
                new_chunks.append({
                    "document_id": doc_id,
                    "content": chunk_text,
                    "embedding": embedding,
                    "token_count": len(chunk_text.split()) # Rough estimate
                })

    # 4. Upload new chunks
    if new_chunks:
        print(f"📤 Uploading {len(new_chunks)} chunks to 'document_chunks'...")
        # Batch upload
        for i in range(0, len(new_chunks), 50):
            batch = new_chunks[i:i+50]
            supabase.table("document_chunks").insert(batch).execute()
        print("✅ Success! Knowledge base rebuilt.")
    else:
        print("❌ No chunks generated.")

if __name__ == "__main__":
    rebuild()
