from supabase import create_client
import os
from dotenv import load_dotenv

# Загружаем основные переменные и секреты
load_dotenv()
load_dotenv(".env.secrets")

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)
