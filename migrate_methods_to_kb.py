import os
import sys
from supabase import create_client
from dotenv import load_dotenv

# Force UTF-8 for windows terminal
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

env_path = r"c:\Users\kirik\Multi-Modal-Agent\.env"
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def migrate():
    print("🚀 Starting migration from lab_methods to knowledge_base...")
    
    # 1. Fetch all methods from lab_methods
    methods_res = supabase.table("lab_methods").select("*").execute()
    methods = methods_res.data
    
    if not methods:
        print("No methods found in 'lab_methods' to migrate.")
        return

    print(f"Found {len(methods)} records in 'lab_methods'.")
    
    new_kb_entries = []
    
    for m in methods:
        name = m.get("method_name") or "Unknown"
        # Format content exactly like structured_uploader.py
        content = f"Название: {name}. "
        if m.get('preparation'): content += f"Подготовка: {m['preparation'][:800]} "
        if m.get('calibration'): content += f"Калибровка: {m['calibration'][:800]} "
        if m.get('measurement'): content += f"Измерение: {m['measurement'][:1200]} "
        if m.get('spectro_setup'): content += f"Настройка: {m['spectro_setup'][:800]} "
        
        entry = {
            "file_source": m.get("file_source", "Migrated"),
            "category": "Structured Method",
            "step_type": "Method",
            "content": content,
            "embedding": m.get("embedding"), # Reuse existing embedding if available
            "metadata": {
                "source": m.get("file_source", "Migrated"),
                "method_name": name,
                "migration_date": "2026-03-12"
            }
        }
        new_kb_entries.append(entry)

    # 2. Upload to knowledge_base
    print(f"Uploading {len(new_kb_entries)} entries to 'knowledge_base'...")
    
    # Batch upload to avoid timeouts
    batch_size = 10
    for i in range(0, len(new_kb_entries), batch_size):
        batch = new_kb_entries[i:i+batch_size]
        try:
            supabase.table("knowledge_base").insert(batch).execute()
            print(f"  Processed batch {i // batch_size + 1}")
        except Exception as e:
            print(f"  Error in batch {i // batch_size + 1}: {e}")

    print("✅ Migration complete!")

if __name__ == "__main__":
    migrate()
