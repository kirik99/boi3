import os
import time
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from supabase import create_client, Client

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("--- Testing HF ---")
try:
    hf_client = InferenceClient(token=HF_TOKEN)
    emb = hf_client.feature_extraction("hello world", model="intfloat/multilingual-e5-large")
    print(f"HF Success! Embedding size: {len(emb) if hasattr(emb, '__len__') else 'unknown'}")
except Exception as e:
    print(f"HF Failed: {e}")

print("\n--- Testing Supabase API ---")
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    # Just a simple check to see if we can reach it
    res = supabase.table("knowledge_base").select("id").limit(1).execute()
    print("Supabase API Success! (or at least reachable)")
except Exception as e:
    print(f"Supabase API Failed: {e}")
