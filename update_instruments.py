import os
import json
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ SUPABASE_URL or SUPABASE_KEY not found in .env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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

def update_instruments():
    print(f"🚀 Updating {len(EQUIPMENT)} instruments in 'lab_methods'...")
    
    for item in EQUIPMENT:
        method_name = item["name"]
        en_name = item["en"]
        
        # Check if already exists
        res = supabase.table("lab_methods").select("id").ilike("method_name", f"%{method_name}%").execute()
        
        if res.data:
            print(f"⏩ Skipping existing instrument: {method_name}")
            continue
            
        # Insert placeholder record
        # Note: We don't have embeddings here, but the RAG pipeline will still search by content if we add text search
        # or we can just add them so they exist in the metadata/list.
        # But for RAG to work, we'd need embeddings. 
        # For now, let's just add them as empty shells that can be filled.
        
        supabase.table("lab_methods").insert({
            "method_name": method_name,
            "file_source": "manual_update",
            "metadata": {"english_name": en_name}
        }).execute()
        print(f"✅ Added: {method_name}")

if __name__ == "__main__":
    update_instruments()
