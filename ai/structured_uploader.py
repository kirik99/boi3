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

print("=== Structured Uploader Script Started ===", flush=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# Using Hugging Face for both LLM and Embeddings
hf_client = InferenceClient(token=HF_TOKEN)

def get_embedding(text):
    """Get vector embedding via HF API"""
    model_id = "intfloat/multilingual-e5-large"
    # Truncate text strictly to avoid overloading (E5-large limit is around 512 tokens)
    # 3000 chars is a safe estimate for ~500-700 tokens
    safe_text = text[:3000] 
    
    try:
        embedding = hf_client.feature_extraction(f"passage: {safe_text}", model=model_id)
        if hasattr(embedding, "tolist"):
            embedding = embedding.tolist()
        if isinstance(embedding, list) and len(embedding) > 0 and isinstance(embedding[0], list):
            return embedding[0]
        return embedding
    except Exception as e:
        err_msg = str(e).lower()
        # Retry on 503 (loading) or connection timeout (10060)
        if "503" in err_msg or "loading" in err_msg or "10060" in err_msg or "timeout" in err_msg:
            print(f"  Connection issue/Model loading ({e}), waiting 20s...")
            time.sleep(20)
            return get_embedding(text)
        raise e

def chunk_text(text, max_chars=18000, overlap=2500):
    """Split text into overlapping chunks to fit LLM context limits.
    Increased max_chars and overlap for better context retention in large manuals."""
    if len(text) <= max_chars:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunks.append(text[start:end])
        start += (max_chars - overlap)
    return chunks

def parse_with_llm(text, context_info=""):
    """Use Hugging Face (Llama 3.1 8B) to structure the raw text in Russian"""
    print(f"  Sending chunk to LLM ({len(text)} chars)...")
    
    model_id = "meta-llama/Llama-3.1-8B-Instruct"
    
    prompt = f"""
    Проанализируй текст лабораторной методики или инструкции к оборудованию на русском языке.
    {context_info}
    
    Твоя задача — извлечь данные и вернуть их СТРОГО в формате JSON списка объектов.
    Если в тексте несколько методов/протоколов, извлеки каждый отдельно.
    Если это инструкция к прибору (manual), выдели основные шаги настройки и эксплуатации как отдельные методы.
    Если этот блок текста является продолжением предыдущего, постарайся сохранить целостность названий методов.

    Поля для каждого объекта:
    - "method_name": Название метода или раздела (обязательно)
    - "preparation": Подготовка проб, реагентов или прибора
    - "calibration": Описание процесса калибровки или стандартизации
    - "measurement": Этапы измерения или основного процесса
    - "spectro_setup": Настройка оборудования (длина волны, кюветы и т.д.)

    ВАЖНО:
    1. Пиши значения полей на РУССКОМ языке.
    2. Если какой-то раздел не найден, заполни поле пустым "".
    3. Верни ТОЛЬКО JSON список [ {{...}}, {{...}} ]. Без вступительных слов и пояснений.
    4. Если полезной информации нет (например, только оглавление или общие слова), верни пустой список [].
    5. Если метод описан частично, извлеки что есть.

    Текст для анализа:
    {text}
    """

    try:
        response = hf_client.chat_completion(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2500,
            temperature=0.1
        )
        content = response.choices[0].message.content.strip()
        
        # Robust JSON extraction
        json_str = ""
        # 1. Try to find content inside code blocks
        code_match = re.search(r"```(?:json)?\s*(.*?)```", content, re.DOTALL)
        if code_match:
            json_str = code_match.group(1).strip()
        else:
            # 2. Try to find the first '[' and last ']'
            start_bracket = content.find('[')
            end_bracket = content.rfind(']')
            if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
                json_str = content[start_bracket:end_bracket+1]
            else:
                # 3. Fallback to first '{' and last '}'
                start_brace = content.find('{')
                end_brace = content.rfind('}')
                if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
                    json_str = content[start_brace:end_brace+1]
        
        if not json_str:
            return []

        try:
            # Fix common tiny errors LLM might make
            data = json.loads(json_str)
            return data if isinstance(data, list) else [data]
        except json.JSONDecodeError as je:
            print(f"  JSON Decode Error: {je}. Attempting aggressive cleaning...")
            # Try to find all JSON-like objects in the string if it's a mess
            try:
                # If it's "Extra data", try to parse only until the error index
                if "Extra data" in str(je):
                    # je.pos is the start of the extra data
                    data = json.loads(json_str[:je.pos])
                    return data if isinstance(data, list) else [data]
            except:
                pass
            
            print(f"  --- RAW LLM RESPONSE START ---")
            print(content)
            print(f"  --- RAW LLM RESPONSE END ---")
            return []
                
    except Exception as e:
        print(f"  HF LLM Error: {e}")
        if "503" in str(e).lower() or "loading" in str(e).lower():
            print("  Model is loading, waiting 30s...")
            time.sleep(30)
            return parse_with_llm(text, context_info)
        return []

def extract_text(file_path):
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
        elif ext in [".txt", ".md"]:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return text

def process_file(file_path, base_dir):
    file_rel_path = os.path.relpath(file_path, base_dir)
    file_name = os.path.basename(file_path)
    print(f"\n[{time.strftime('%H:%M:%S')}] Processing {file_rel_path}...", flush=True)
    
    raw_text = extract_text(file_path)
    if not raw_text or not raw_text.strip():
        print(f"  Empty text extracted from {file_name}")
        return

    # Split into chunks if necessary
    chunks = chunk_text(raw_text)
    total_chunks = len(chunks)
    
    unique_methods = {} # To deduplicate if overlapping chunks find same method
    
    for idx, chunk in enumerate(chunks):
        if total_chunks > 1:
            print(f"  Chunk {idx+1}/{total_chunks}")
        
        context = f"Это часть {idx+1} из {total_chunks} файла {file_name}."
        protocols = parse_with_llm(chunk, context)
        
        for p in protocols:
            if not isinstance(p, dict): continue
            name = p.get("method_name", "Unknown").strip()
            if name == "Unknown" or len(name) < 3: continue
            
            # Simple deduplication by name
            if name in unique_methods:
                # Merge fields if they have more content
                for field in ["preparation", "calibration", "measurement", "spectro_setup"]:
                    if len(p.get(field, "")) > len(unique_methods[name].get(field, "")):
                        unique_methods[name][field] = p[field]
            else:
                p["file_source"] = file_rel_path
                unique_methods[name] = p

    # Upload unique protocols
    for name, p in unique_methods.items():
        # Build searchable string - prioritize key fields for embedding
        # E5-large handles about 512 tokens. 
        # We construct a summary that hits all important parts.
        search_text = f"Название: {name}. "
        if p.get('preparation'): search_text += f"Подготовка: {p['preparation'][:800]} "
        if p.get('calibration'): search_text += f"Калибровка: {p['calibration'][:800]} "
        if p.get('measurement'): search_text += f"Измерение: {p['measurement'][:1200]} "
        if p.get('spectro_setup'): search_text += f"Настройка: {p['spectro_setup'][:800]} "
        
        print(f"  Generating embedding for: {name} ({len(search_text)} chars)")
        embedding = get_embedding(search_text)
        
        data = {
            "file_source": p.get("file_source", "Unknown"),
            "category": "Structured Method",
            "step_type": "Method",
            "content": search_text,
            "embedding": embedding,
            "metadata": {
                "source": p.get("file_source", "Unknown"),
                "method_name": name,
                "processed_at": time.strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        
        try:
            supabase.table("knowledge_base").insert(data).execute()
            print(f"  [SUCCESS] Saved: {name} to knowledge_base")
        except Exception as e:
            print(f"  [ERROR] Failed to save {name}: {e}")

def main():
    target_dir = r"C:\Users\kirik\Multi-Modal-Agent\inf"
    
    if not os.path.exists(target_dir):
        print(f"Target directory not found: {target_dir}")
        return

    # Recursive scan
    files_to_process = []
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if file.lower().endswith((".pdf", ".docx", ".txt", ".md")):
                files_to_process.append(os.path.join(root, file))
    
    print(f"Found {len(files_to_process)} files to process in {target_dir}", flush=True)
    
    for file_path in files_to_process:
        process_file(file_path, target_dir)

if __name__ == "__main__":
    main()
