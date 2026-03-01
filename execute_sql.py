# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Extract project ref from URL if possible, or use env
# postgresql://postgres.[REF]:[PASS]@...
import re
match = re.search(r"postgres\.([^:]+):([^@]+)@", DATABASE_URL)
if match:
    PROJECT_REF = match.group(1)
    PASSWORD = match.group(2)
else:
    PROJECT_REF = os.getenv("SUPABASE_PROJECT_REF", "inlnzpjewdyovotnidsy")
    PASSWORD = os.getenv("SUPABASE_DB_PASSWORD", "")

# Explicit URL for Pooler in Transaction Mode (6543) with SSL
URL = f"postgresql://postgres.{PROJECT_REF}:{PASSWORD}@aws-0-eu-central-1.pooler.supabase.com:6543/postgres?sslmode=require"

def execute_sql_file(file_path):
    print(f"Executing {file_path} via Pooler 6543...")
    try:
        conn = psycopg2.connect(URL)
        conn.autocommit = True
        cur = conn.cursor()
        with open(file_path, 'r', encoding='utf-8') as f:
            sql = f.read()
        cur.execute(sql)
        print("SQL execution successful.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Final attempt failed: {e}")

if __name__ == "__main__":
    execute_sql_file("setup_db.sql")
