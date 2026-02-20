# Team Setup Guide

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Multi-Modal-Agent
```

### 2. Install Dependencies

```bash
# Node.js dependencies
npm install

# Python dependencies (for embeddings)
pip install -r requirements.txt
```

### 3. Setup Environment Variables

Create `.env` file in the root directory with your API keys:

```
OPENROUTER_API_KEY=your_openrouter_api_key
SUPABASE_KEY=your_supabase_anon_key
HF_TOKEN=your_huggingface_token
```

**Get your API keys:**
- **OpenRouter**: https://openrouter.ai/keys
- **Supabase**: Project Settings → API → anon/public key
- **Hugging Face**: https://huggingface.co/settings/tokens

### 4. Setup Supabase Database

1. Go to Supabase Dashboard → SQL Editor
2. Run the following SQL to enable vector search:

```sql
-- Enable pgvector extension
create extension if not exists vector;

-- Add embedding column
alter table documents 
add column if not exists embedding vector(384);

-- Create index for similarity search
create index if not exists documents_embedding_idx 
on documents using ivfflat (embedding vector_cosine_ops)
with (lists = 100);
```

### 5. Seed Test Data (Optional)

```bash
python seed_data.py
```

### 6. Run Development Server

```bash
npm run dev
```

App will be available at: http://localhost:5000

---

## Project Structure

```
Multi-Modal-Agent/
├── client/          # React frontend
├── server/          # Node.js backend
├── shared/          # Shared types and schemas
├── embedding.py     # Hugging Face embeddings
├── supabase_client.py  # Supabase client
├── .env             # Environment variables (API keys - DO NOT COMMIT)
└── requirements.txt # Python dependencies
```

---

## Security Notes

- ⚠️ **NEVER** commit `.env` with API keys to Git
- ✅ Add `.env` to `.gitignore`
- ✅ Rotate API keys if accidentally exposed
- ✅ Use separate Supabase projects for dev/staging/production

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `python seed_data.py` | Seed test data to Supabase |

---

## Troubleshooting

### Python not found
Install Python 3.10+ from https://python.org

### Module not found: supabase
```bash
pip install supabase python-dotenv
```

### Module not found: sentence-transformers
```bash
pip install sentence-transformers
```

### Port 5000 already in use
Edit `dev_server.mjs` and change the port number.

---

## Team Members

Add your team members as collaborators on GitHub:
1. Go to Repository Settings → Collaborators
2. Click "Add people"
3. Enter GitHub username
