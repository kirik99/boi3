import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

s = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("--- Knowledge Base ---")
kb = s.table('knowledge_base').select('id, content').ilike('content', '%Раздел%').limit(5).execute()
print(f"Sample KB: {kb.data}")

master = s.table('knowledge_base').select('id, content').ilike('content', '%Список оборудования%').execute()
print(f"Master List Found: {len(master.data)} rows")
if master.data:
    print(f"Content snippet: {master.data[0]['content'][:100]}...")

print("\n--- Lab Methods ---")
lm = s.table('lab_methods').select('id, method_name').limit(5).execute()
print(f"Sample LM: {lm.data}")
