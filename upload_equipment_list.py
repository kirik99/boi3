import os
import json
import time
from supabase import create_client
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

if not SUPABASE_URL or not SUPABASE_KEY or not HF_TOKEN:
    print("❌ Environment variables missing (SUPABASE_URL, SUPABASE_KEY, or HF_TOKEN)")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
hf_client = InferenceClient(token=HF_TOKEN)
MODEL_ID = "intfloat/multilingual-e5-large"

# User-provided equipment list
EQUIPMENT = [
    {"name": "Анализатор влажности (Shimadzu MOC-120H)", "en": "Moisture Analyzer (MOC-120H)"},
    {"name": "Баня водяная (Loip lb-163)", "en": "Heated bath (Loip lb-163)"},
    {"name": "Ваккуумный насос (VP30)", "en": "Vacuum Pump (VP30)"},
    {"name": "Измельчитель-смеситель (Retsch GM-200)", "en": "Rotor mill (Retsch GM-200)"},
    {"name": "Испаритель ротационный (Lab Tech EV311-V Plus)", "en": "Rotary Evaporator (Lab Tech EV311-V Plus)"},
    {"name": "Испаритель-концентратор (biochromato c1)", "en": "Evaporator-concentrator (biochromato c1)"},
    {"name": "Испытательная машина (Shimadzu модель EZ-LX-0,5)", "en": "Tensile Tester (Shimadzu EZ-LX-0,5)"},
    {"name": "Колбонагреватель (LTH 500)", "en": "Heating mantle (LTH 500)"},
    {"name": "Мешалка верхнеприводная (IKA Eurostar 20 digital)", "en": "Vertical laboratory stirrer (IKA Eurostar 20 digital)"},
    {"name": "ПЦР real-time - Термоциклер (Bio-Rad С1000 Touch cfx96)", "en": "Real-Time PCR Detection System (CFX96 Touch)"},
    {"name": "ПЦР. Термоциклер (Bio-Rad С1000)", "en": "Real-Time PCR Detection System (CFX96 Touch)"},
    {"name": "Спектрофотометр ИК (Shimadzu IRAffinity-1)", "en": "Fourier Transform Infrared (FTIR) spectrophotometer (Shimadzu IRAffinity-1)"},
    {"name": "Спектрофотометр УФ (Shimadzu UV-2600)", "en": "UV spectrophotometer (Shimadzu UV-2600)"},
    {"name": "Сушильный шкаф (Binder FD-53)", "en": "Drying oven (Binder FD-53)"},
    {"name": "Ультразвуковой аппарат (Sonopuls mini20, Bandelin)", "en": "Ultrasonic device (Sonopuls mini20, Bandelin)"},
    {"name": "Шкаф вытяжной лабораторный (ШВЛ-0,5.5)", "en": "Fume hood (ШВЛ-0,5.5)"}
]

def get_embedding(text):
    """Generate embedding for vector search"""
    try:
        embedding = hf_client.feature_extraction(f"passage: {text}", model=MODEL_ID)
        if hasattr(embedding, "tolist"):
            embedding = embedding.tolist()
        if isinstance(embedding, list) and len(embedding) > 0 and isinstance(embedding[0], list):
            return embedding[0]
        return embedding
    except Exception as e:
        print(f"  Embedding Error for '{text[:20]}...': {e}")
        return None

def update_database():
    print(f"🚀 Updating Master Equipment List and Lab Methods...")
    
    # 1. Create a Master Equipment List in knowledge_base
    equipment_names = [item["name"] for item in EQUIPMENT]
    master_list_text = "Список оборудования в лаборатории:\n- " + "\n- ".join(equipment_names)
    
    print(f"📝 Uploading Master Equipment List to 'knowledge_base'...")
    embedding = get_embedding(master_list_text)
    if embedding:
        supabase.table("knowledge_base").insert({
            "content": master_list_text,
            "embedding": embedding,
            "file_source": "system_master_list",
            "metadata": {"type": "equipment_list"}
        }).execute()
        print("✅ Master List Saved.")

    # 2. Update/Insert each instrument in lab_methods
    for item in EQUIPMENT:
        name = item["name"]
        en_name = item["en"]
        
        print(f"🛠 Processing: {name}")
        # Search text for embedding should include both names
        search_text = f"Название прибора: {name}. English name: {en_name}. Оборудование лаборатории."
        embedding = get_embedding(search_text)
        
        if not embedding:
            continue

        # Check if already exists by name
        res = supabase.table("lab_methods").select("id").ilike("method_name", f"%{name}%").execute()
        
        data = {
            "method_name": name,
            "embedding": embedding,
            "file_source": "manual_update",
            "metadata": {"english_name": en_name, "is_placeholder": True}
        }

        if res.data:
            # Update existing record (only embedding and metadata if is_placeholder)
            supabase.table("lab_methods").update(data).eq("id", res.data[0]["id"]).execute()
            print(f"✅ Updated: {name}")
        else:
            # Insert new record
            supabase.table("lab_methods").insert(data).execute()
            print(f"✅ Inserted: {name}")

if __name__ == "__main__":
    update_database()
