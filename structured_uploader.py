import os
import json
import requests
import time
import re
from pypdf import PdfReader
from docx import Document
from dotenv import load_dotenv
from supabase import create_client, Client
from pathlib import Path
from huggingface_hub import InferenceClient

import sys
import io

# Load environment variables
load_dotenv()

# Force UTF-8 for console output to handle Russian characters correctly
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# Using Hugging Face for both LLM and Embeddings
hf_client = InferenceClient(token=HF_TOKEN)

def get_embedding(text):
    """Get vector embedding via HF API"""
    model_id = "intfloat/multilingual-e5-large"
    try:
        embedding = hf_client.feature_extraction(f"passage: {text}", model=model_id)
        if hasattr(embedding, "tolist"):
            embedding = embedding.tolist()
        if isinstance(embedding, list) and len(embedding) > 0 and isinstance(embedding[0], list):
            return embedding[0]
        return embedding
    except Exception as e:
        if "503" in str(e):
            print("  Model loading, waiting 20s...")
            time.sleep(20)
            return get_embedding(text)
        raise e

def parse_with_llm(text):
    """Use Hugging Face (Llama 3.1 8B) to structure the raw text in Russian"""
    print("  Sending text to Hugging Face for structured parsing...")
    
    # Llama-3.1-8B-Instruct is much more capable for structured extraction
    model_id = "meta-llama/Llama-3.1-8B-Instruct"
    
    prompt = f"""
    Проанализируй текст лабораторной методики на русском языке.
    В тексте может быть один или несколько протоколов.
    
    Твоя задача — извлечь данные и вернуть их СТРОГО в формате JSON списка объектов.
    
    Поля для каждого объекта:
    - "method_name": Название метода
    - "preparation": Этапы приготовления реагентов
    - "calibration": Этапы калибровки
    - "measurement": Этапы измерения
    - "spectro_setup": Настройка и включение спектрофотометра (если есть общая инструкция в конце файла, добавь её в это поле для каждого найденного метода)

    ВАЖНО: Пиши значения полей на РУССКОМ языке.
    Если какой-то раздел не найден, оставь поле пустым "".
    
    Верни ТОЛЬКО JSON список. Без лишних слов.

    Текст для анализа:
    {text}
    """

    try:
        response = hf_client.chat_completion(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.1
        )
        content = response.choices[0].message.content.strip()
        print(f"  --- LLM Response Raw --- \n{content[:200]}...\n  ---") # Debug print

        # Search for JSON array in the response
        json_match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            return data if isinstance(data, list) else [data]
        
        # Try finding a single object if it's not a list
        dict_match = re.search(r'\{.*\}', content, re.DOTALL)
        if dict_match:
            data = json.loads(dict_match.group(0))
            return [data] if isinstance(data, dict) else []

        return []
    except Exception as e:
        print(f"  HF LLM Error: {e}")
        if "503" in str(e):
            print("  Model is loading, waiting 30s...")
            time.sleep(30)
            return parse_with_llm(text)
        return []

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
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return text

def main():
    target_dir = r"C:\Users\kirik\Multi-Modal-Agent\inf"
    
    for file in os.listdir(target_dir):
        if file.endswith((".pdf", ".docx", ".txt")):
            file_path = os.path.join(target_dir, file)
            print(f"Processing {file}...")
            
            raw_text = extract_text(file_path)
            if not raw_text.strip(): continue
            
            # Split text if too large for LLM context (simple split)
            protocols = parse_with_llm(raw_text)
            print(f"  Detected {len(protocols)} protocols.")
            
            for p in protocols:
                if not isinstance(p, dict): continue
                name = p.get("method_name", "Unknown")
                print(f"  Uploading protocol: {name}")
                
                full_content = f"{name} {p.get('preparation','')} {p.get('calibration','')} {p.get('measurement','')} {p.get('spectro_setup','')}"
                embedding = get_embedding(full_content)
                
                data = {
                    "method_name": name,
                    "preparation": p.get("preparation", ""),
                    "calibration": p.get("calibration", ""),
                    "measurement": p.get("measurement", ""),
                    "spectro_setup": p.get("spectro_setup", ""),
                    "file_source": file,
                    "embedding": embedding,
                    "metadata": {"source": file}
                }
                
                try:
                    supabase.table("lab_methods").insert(data).execute()
                    print(f"  Successfully saved {name}")
                except Exception as e:
                    print(f"  Error inserting {name}: {e}")

if __name__ == "__main__":
    main()
