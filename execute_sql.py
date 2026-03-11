import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    """Try various connection strings to handle Supabase pooler quirks"""
    # 1. Try provided DATABASE_URL
    if DATABASE_URL:
        try:
            return psycopg2.connect(DATABASE_URL)
        except Exception as e:
            print(f"Direct connection failed: {e}")

    # 2. Try to construct direct hostname (bypassing pooler if possible)
    # The project ref is likely in the URL
    project_ref = os.getenv("SUPABASE_PROJECT_REF")
    password = os.getenv("SUPABASE_DB_PASSWORD")
    
    if project_ref and password:
        direct_url = f"postgresql://postgres:{password}@db.{project_ref}.supabase.co:5432/postgres"
        try:
            print(f"Attempting direct connection to db.{project_ref}.supabase.co...")
            return psycopg2.connect(direct_url)
        except Exception as e:
            print(f"Direct construction failed: {e}")
            raise e
    
    raise Exception("Could not establish database connection. Please check DATABASE_URL or SUPABASE_PROJECT_REF/SUPABASE_DB_PASSWORD environment variables.")

def execute_sql_file(file_path):
    print(f"Executing {file_path}...")
    try:
        conn = get_connection()
        conn.autocommit = True
        cur = conn.cursor()
        with open(file_path, 'r', encoding='utf-8') as f:
            sql = f.read()
        cur.execute(sql)
        print("SQL execution successful.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    execute_sql_file("setup_db.sql")
