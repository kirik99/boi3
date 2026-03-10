import os
import json
import requests
import time
import sys
import io
from pypdf import PdfReader
from docx import Document
from dotenv import load_dotenv
from supabase import create_client, Client
from pathlib import Path
from huggingface_hub import InferenceClient

# Load environment variables
load_dotenv()

# Force UTF-8 for console output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=== Raw Chunk Uploader Script Started ===", flush=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
hf_client = InferenceClient(token=HF_TOKEN)

def get_embedding(text):
    """Get vector embedding via HF API with retries"""
    model_id = "intfloat/multilingual-e5-large"
    # E5 models are optimized for ~512 tokens. 
    # 2500 chars is roughly 500-600 tokens.
    safe_text = text[:2500] 
    
    try:
        embedding = hf_client.feature_extraction(f"passage: {safe_text}", model=model_id)
        if hasattr(embedding, "tolist"):
            embedding = embedding.tolist()
        if isinstance(embedding, list) and len(embedding) > 0 and isinstance(embedding[0], list):
            return embedding[0]
        return embedding
    except Exception as e:
        err_msg = str(e).lower()
        if "503" in err_msg or "loading" in err_msg or "timeout" in err_msg:
            print(f"  HF Model loading/timeout ({e}), waiting 20s...")
            time.sleep(20)
            return get_embedding(text)
        raise e

def extract_text(file_path):
    """Robust text extraction for multiple formats"""
    ext = Path(file_path).suffix.lower()
    text = ""
    try:
        if ext == ".pdf":
            reader = PdfReader(file_path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        elif ext == ".docx":
            doc = Document(file_path)
            text = "\n".join([p.text for p in doc.paragraphs])
        elif ext in [".txt", ".md", ".py"]:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
    except Exception as e:
        print(f"  Error reading {file_path}: {e}")
    return text

def chunk_text(text, chunk_size=1200, overlap=250):
    """Splits text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
    return chunks

def process_file(file_path, base_dir):
    file_rel_path = os.path.relpath(file_path, base_dir)
    file_name = os.path.basename(file_path)
    print(f"\n[{time.strftime('%H:%M:%S')}] Chunking: {file_rel_path}...", flush=True)
    
    raw_text = extract_text(file_path)
    if not raw_text or not raw_text.strip():
        print(f"  No text found in {file_name}")
        return

    chunks = chunk_text(raw_text)
    total_chunks = len(chunks)
    
    for i, chunk in enumerate(chunks):
        if i % 5 == 0 or i == total_chunks - 1:
            print(f"  Uploading chunk {i+1}/{total_chunks}...")
        
        try:
            embedding = get_embedding(chunk)
            
            data = {
                "file_source": file_rel_path,
                "category": "Lab Document",
                "step_type": "Raw Chunk",
                "content": chunk,
                "embedding": embedding,
                "metadata": {
                    "source": file_rel_path,
                    "chunk_index": i,
                    "total_chunks": total_chunks,
                    "processed_at": time.strftime('%Y-%m-%d %H:%M:%S')
                }
            }
            
            supabase.table("knowledge_base").insert(data).execute()
        except Exception as e:
            print(f"  [ERROR] Chunk {i} failed: {e}")
            time.sleep(1)

def main():
    target_dir = r"C:\Users\kirik\Multi-Modal-Agent\inf"
    
    if not os.path.exists(target_dir):
        print(f"Target directory not found: {target_dir}")
        return

    files_to_process = []
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if file.lower().endswith((".pdf", ".docx", ".txt", ".md")):
                files_to_process.append(os.path.join(root, file))
    
    print(f"Found {len(files_to_process)} files for raw chunking in {target_dir}")
    
    for file_path in files_to_process:
        process_file(file_path, target_dir)

if __name__ == "__main__":
    main()
