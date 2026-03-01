import os
import re
from pypdf import PdfReader
from docx import Document
from dotenv import load_dotenv
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Using a local model for embeddings to ensure consistency and speed
# 'sentence-transformers/all-mpnet-base-v2' or 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2' (for Russian)
# Dimensions for 'paraphrase-multilingual-MiniLM-L12-v2' is 384, let's adjust the SQL if needed or use a larger one.
# Given the SQL used 1024, let's use 'intfloat/multilingual-e5-large' (1024 dimensions)
embed_model = SentenceTransformer('intfloat/multilingual-e5-large')

def get_embedding(text):
    # For E5 models, it's recommended to prefix with "passage: "
    embedding = embed_model.encode(f"passage: {text}")
    return embedding.tolist()

def parse_pdf(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    
    sections = []
    
    # 1. Spectrophotometer setup
    spectro_match = re.search(r"Настройка и подключение спектрофотометра(.*?)(?=---|$)", text, re.S | re.I)
    if spectro_match:
        sections.append({
            "category": "Spectrophotometer",
            "step_type": "Power-on",
            "content": spectro_match.group(1).strip(),
            "file_source": "1.pdf"
        })
    
    # 2. Method DPPH
    patterns = {
        "Preparation": r"Приготовление DPPH(.*?)(?=Калибровка|$)",
        "Calibration": r"Калибровка по Trolox(.*?)(?=Измерение|$)",
        "Measurement": r"Измерение образца(.*?)(?=Настройка|$)"
    }
    
    for step, pattern in patterns.items():
        match = re.search(pattern, text, re.S | re.I)
        if match:
            sections.append({
                "category": "Method (DPPH)",
                "step_type": step,
                "content": match.group(1).strip(),
                "file_source": "1.pdf"
            })
            
    return sections

def parse_docx(path):
    doc = Document(path)
    text = "\n".join([p.text for p in doc.paragraphs])
    
    sections = []
    
    # Method Phenols
    patterns = {
        "Preparation": r"Приготовление реагентов Фенолы(.*?)(?=Калибровка|$)",
        "Calibration": r"Калибровка по галловой кислоте(.*?)(?=Измерение|$)",
        "Measurement": r"Измерение образца(.*?)(?=$)"
    }
    
    for step, pattern in patterns.items():
        match = re.search(pattern, text, re.S | re.I)
        if match:
            sections.append({
                "category": "Method (Phenols)",
                "step_type": step,
                "content": match.group(1).strip(),
                "file_source": "2.docx"
            })
            
    return sections

def main():
    pdf_path = r'C:\Users\kirik\Multi-Modal-Agent\inf\1.pdf'
    docx_path = r'C:\Users\kirik\Multi-Modal-Agent\inf\2.docx'
    
    all_sections = []
    print("Parsing documents...")
    all_sections.extend(parse_pdf(pdf_path))
    all_sections.extend(parse_docx(docx_path))
    
    print(f"Found {len(all_sections)} sections. Vectorizing and uploading...")
    
    for sec in all_sections:
        print(f"Processing: {sec['category']} - {sec['step_type']}")
        embedding = get_embedding(sec['content'])
        
        data = {
            "file_source": sec['file_source'],
            "category": sec['category'],
            "step_type": sec['step_type'],
            "content": sec['content'],
            "embedding": embedding,
            "metadata": {"source": sec['file_source'], "type": sec['step_type']}
        }
        
        try:
            response = supabase.table("knowledge_base").insert(data).execute()
            print(f"Successfully uploaded {sec['step_type']}")
        except Exception as e:
            print(f"Error uploading {sec['step_type']}: {e}")

if __name__ == "__main__":
    main()
