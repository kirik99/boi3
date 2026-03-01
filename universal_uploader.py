import os
import re
import requests
import time
from pypdf import PdfReader
from docx import Document
from dotenv import load_dotenv
from supabase import create_client, Client
from pathlib import Path
from huggingface_hub import InferenceClient

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# Initialize HF client
hf_client = InferenceClient(token=HF_TOKEN)

def get_embedding(text):
    """Call Hugging Face Inference API to get embeddings using the official client"""
    model_id = "intfloat/multilingual-e5-large"
    
    try:
        # E5 models require "passage: " prefix for indexing
        # feature_extraction returns a nested list or array
        embedding = hf_client.feature_extraction(f"passage: {text}", model=model_id)
        
        # Convert to list if it's a numpy array
        if hasattr(embedding, "tolist"):
            embedding = embedding.tolist()
        
        # Result might be nested [[...]]
        if isinstance(embedding, list) and len(embedding) > 0 and isinstance(embedding[0], list):
            return embedding[0]
        return embedding
    except Exception as e:
        if "503" in str(e) or "loading" in str(e).lower():
            print("  Model is loading on HF, waiting 20s...")
            time.sleep(20)
            return get_embedding(text)
        raise e

def extract_text(file_path):
    ext = Path(file_path).suffix.lower()
    text = ""
    
    try:
        if ext == ".pdf":
            reader = PdfReader(file_path)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        elif ext == ".docx":
            doc = Document(file_path)
            text = "\n".join([p.text for p in doc.paragraphs])
        elif ext in [".txt", ".md", ".py", ".js", ".html", ".css", ".csv"]:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        
    return text

def chunk_text(text, chunk_size=1000, overlap=100):
    """Splits text into chunks. HF API has token limits (~512 tokens)."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
    return chunks

def upload_file(file_path):
    print(f"Processing: {file_path}")
    text = extract_text(file_path)
    if not text.strip():
        print(f"Skipping empty file: {file_path}")
        return

    chunks = chunk_text(text)
    file_name = os.path.basename(file_path)
    
    for i, chunk in enumerate(chunks):
        print(f"  Vectorizing and uploading chunk {i+1}/{len(chunks)} via HF API...")
        try:
            embedding = get_embedding(chunk)
            
            data = {
                "file_source": file_name,
                "category": "General",
                "step_type": "Chunk",
                "content": chunk,
                "embedding": embedding,
                "metadata": {
                    "source": file_name,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "extension": Path(file_path).suffix
                }
            }
            
            supabase.table("knowledge_base").insert(data).execute()
        except Exception as e:
            print(f"  Error processing chunk {i}: {e}")
            time.sleep(1)

def main():
    target_dir = r"C:\Users\kirik\Multi-Modal-Agent\inf"
    
    if not os.path.exists(target_dir):
        print(f"Directory {target_dir} not found.")
        return

    for root, dirs, files in os.walk(target_dir):
        for file in files:
            # Skip existing process scripts
            if file in ["upload_to_supabase.py", "universal_uploader.py", "execute_sql.py"]:
                continue
            file_path = os.path.join(root, file)
            upload_file(file_path)

if __name__ == "__main__":
    main()
