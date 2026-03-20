import os
import requests
import logging
import sqlite3
import json
from supabase import create_client
from dotenv import load_dotenv
from embedding import get_embedding

# Setup exact match cache for RAG
rag_cache_conn = sqlite3.connect('rag_cache.db', check_same_thread=False)
rag_cache_conn.execute('CREATE TABLE IF NOT EXISTS rag_cache (query TEXT PRIMARY KEY, result TEXT)')
rag_cache_conn.commit()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("SUPABASE_URL or SUPABASE_KEY not found in .env")
    raise ValueError("Missing Supabase credentials")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def expand_query(query):
    """Step 0: Query Expansion using DeepSeek."""
    if not DEEPSEEK_API_KEY:
        return query
    logger.info("🔍 Expanding query with DeepSeek...")
    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "Ты - умный поисковый ассистент лаборатории. Пользователь даст тебе запрос. Верни ТОЛЬКО 3-5 ключевых синонимов или терминов через пробел, без никаких дополнительных слов, приветствий или форматирования."},
                {"role": "user", "content": query}
            ],
            "temperature": 0.1
        }
        res = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=data, timeout=5)
        res.raise_for_status()
        expanded = res.json()["choices"][0]["message"]["content"].strip()
        logger.info(f"✨ Query expanded terms: {expanded}")
        return query + " " + expanded
    except Exception as e:
        logger.error(f"❌ Query expansion failed: {e}")
        return query

def retrieve_from_lab_methods(query, query_embedding, match_threshold=0.2, match_count=5):
    """Step 1: High Priority Retrieval from lab_methods."""
    logger.info("🔍 Searching in 'lab_methods'...")
    results = []
    
    try:
        rpc_res = supabase.rpc("match_methods", {
            "query_embedding": query_embedding,
            "match_threshold": match_threshold,
            "match_count": match_count
        }).execute()
        
        if rpc_res.data:
            logger.info(f"✅ Found {len(rpc_res.data)} matches in 'lab_methods'")
            results.extend([{
                "content": f"Instrument: {r.get('method_name')}\nPreparation: {r.get('preparation')}\nCalibration: {r.get('calibration')}\nMeasurement: {r.get('measurement')}\nSpectro Setup: {r.get('spectro_setup')}",
                "source": "lab_methods",
                "similarity": r.get("similarity")
            } for r in rpc_res.data])
    except Exception as e:
        logger.error(f"❌ Error in match_methods: {e}")
    
    # Text-based fallback (more robust)
    if not results:
        logger.info("🔍 Keyword searching in 'lab_methods'...")
        # Extract keywords (words > 3 chars), ignore generic words
        stop_words = {"информация", "базы", "база", "данных", "данные", "поиск", "все"}
        keywords = [w.strip(",.!?") for w in query.split() if len(w) > 3 and w.lower() not in stop_words]
        if keywords:
            try:
                # Build OR filter for keywords using correct PostgREST syntax
                filter_str = ",".join([f"method_name.ilike.%{k}%" for k in keywords])
                text_res = supabase.table("lab_methods").select("*").or_(filter_str).limit(match_count).execute()
                if text_res.data:
                    results.extend([{
                        "content": f"Instrument: {r.get('method_name')}\nPreparation: {r.get('preparation')}\nCalibration: {r.get('calibration')}\nMeasurement: {r.get('measurement')}\nSpectro Setup: {r.get('spectro_setup')}",
                        "source": "lab_methods (text search)",
                        "similarity": 0.5
                    } for r in text_res.data])
            except Exception as e:
                logger.error(f"❌ Error in lab_methods text search: {e}")

    return results

def retrieve_from_knowledge_base(query, query_embedding, match_threshold=0.12, match_count=10):
    """Step 2: Vector Search in knowledge_base with text fallback."""
    logger.info("🔍 Searching in 'knowledge_base'...")
    results = []
    try:
        rpc_res = supabase.rpc("match_chunks", {
            "query_embedding": query_embedding,
            "match_threshold": match_threshold,
            "match_count": 15  # Reduced from 30 based on user feedback
        }).execute()
        
        if rpc_res.data:
            logger.info(f"✅ Found {len(rpc_res.data)} matches in 'knowledge_base'")
            file_counts = {}
            for r in rpc_res.data:
                src = r.get("file_source", "Unknown")
                # Diversity filter: max 2 chunks per file from vector search
                if file_counts.get(src, 0) < 2:
                    results.append({
                        "content": str(r.get("content")),
                        "source": src,
                        "similarity": r.get("similarity")
                    })
                    file_counts[src] = file_counts.get(src, 0) + 1
    except Exception as e:
        logger.error(f"❌ Error in match_chunks: {e}")
    
    # Text-based fallback for chunks
    if not results:
        logger.info("🔍 Keyword searching in 'knowledge_base'...")
        # Extract keywords, ignore stop words
        important_words = ["оборудование", "прибор", "список", "инструкция", "метод"]
        stop_words = {"информация", "базы", "база", "данных", "данные", "поиск", "все", "какие", "есть"}
        query_words = [w.strip(",.!?").lower() for w in query.split() if len(w) > 3 and w.lower() not in stop_words]
        
        # If any query word or important word matches
        search_terms = list(set(query_words + important_words))
        try:
            # Try to find the master list specifically for general equipment questions
            if any(w in query.lower() for w in ["оборудование", "какие", "что есть"]):
                 text_res = supabase.table("knowledge_base").select("*").ilike("content", "%Список оборудования%").limit(1).execute()
                 if text_res.data:
                     results.append({
                        "content": text_res.data[0].get("content"),
                        "source": "system_master_list",
                        "similarity": 0.6
                     })
            
            if not results:
                # Generic text search using correct PostgREST syntax
                filter_str = ",".join([f"content.ilike.%{k}%" for k in query_words[:3]])
                if filter_str:
                    text_res = supabase.table("knowledge_base").select("*").or_(filter_str).limit(15).execute()
                    if text_res.data:
                        file_counts_text = {}
                        for r in text_res.data:
                            src = r.get("file_source", "Unknown")
                            # Diversity filter: max 2 chunks per file from text search
                            if file_counts_text.get(src, 0) < 2:
                                results.append({
                                    "content": str(r.get("content")),
                                    "source": src + " (text search)",
                                    "similarity": 0.5
                                })
                                file_counts_text[src] = file_counts_text.get(src, 0) + 1
        except Exception as e:
            logger.error(f"❌ Error in knowledge_base text search: {e}")

    return results

def internet_search_fallback(query):
    """Step 3: Internet Fallback."""
    logger.info(f"🌐 Performing internet fallback for: {query}")
    # Using DuckDuckGo Lite for simple text-based results
    try:
        search_url = f"https://duckduckgo.com/html/?q={query}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # This is a very basic extraction. In a real scenario, use BeautifulSoup.
        # For now, we return a message indicating an attempt was made.
        return [{
            "content": f"I couldn't find specific instructions in our local database for '{query}'. Based on a general search, please ensure you are following the manufacturer's manual for this specific instrument.",
            "source": "Internet Search",
            "similarity": 0
        }]
    except Exception as e:
        logger.error(f"❌ Internet search failed: {e}")
    
    return []

def rag_query(query):
    """Main RAG Pipeline using unified knowledge_base table."""
    logger.info(f"🚀 Processing RAG query: {query}")
    
    # Check cache first
    cached = rag_cache_conn.execute('SELECT result FROM rag_cache WHERE query = ?', (query,)).fetchone()
    if cached:
        logger.info(f"✨ Found exact match in cache for query: {query}")
        return json.loads(cached[0])
    
    # Check if user explicitly asks for internet
    force_internet = any(word in query.lower() for word in ["интернет", "сеть", "internet", "web"])
    
    # Expand Query
    expanded_query = expand_query(query)
    
    # Get embedding
    embedding = get_embedding(expanded_query)
    if not embedding:
        logger.warning("⚠️ Failed to generate embedding.")
        return {"results": [], "source": "None"}

    all_results = []
    
    # Unified Search in knowledge_base (Table 2) 
    kb_results = retrieve_from_knowledge_base(query, embedding)
    if kb_results:
        all_results.extend(kb_results)
    
    # Optional Fallback: Internet
    source = "database"
    if not all_results or force_internet:
        internet_results = internet_search_fallback(query)
        all_results.extend(internet_results)
        source = "internet" if not kb_results else "mixed"
    
    if all_results:
        # Re-rank to prioritize short Russian sources
        def score_result(r):
            score = float(r.get("similarity", 0.0))
            content = str(r.get("content", ""))
            
            # Bonus for Russian text (cyrillic characters)
            if any('\u0400' <= c <= '\u04FF' for c in content[:200]):
                score += 0.35
                
            # Bonus for short instructions, penalty for long theoretical blocks
            length = len(content)
            if length < 600:
                score += 0.2
            elif length < 1000:
                score += 0.1
            elif length > 2000:
                score -= 0.1
                
            return score
            
        # Deduplicate exactly and apply re-ranking
        seen = set()
        unique_results = []
        for r in all_results:
            snippet = str(r.get("content", ""))[:200]
            if snippet not in seen:
                seen.add(snippet)
                r["similarity"] = score_result(r)
                unique_results.append(r)
                
        # Sort by customized score descending
        unique_results.sort(key=lambda x: float(x.get("similarity", 0.0)), reverse=True)
        
        # Take the best 8 after re-ranking
        all_results = unique_results[:8]
        
    res = {"results": all_results, "source": source}
    rag_cache_conn.execute('INSERT OR REPLACE INTO rag_cache (query, result) VALUES (?, ?)', (query, json.dumps(res)))
    rag_cache_conn.commit()
    return res

if __name__ == "__main__":
    import sys
    # Force UTF-8 for windows terminal
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # Test
    test_q = "какое оборудование есть в лаборатории"
    response: dict = rag_query(test_q)
    print(f"\nFinal Response for '{test_q}' (Source: {response.get('source')}):")
    results = response.get('results', [])
    for r in results:
        if isinstance(r, dict):
            src = r.get('source', 'Unknown')
            cnt = r.get('content', '')
            # Convert to string and slice safely
            content_str = str(cnt)[:100].replace('\n', ' ')
            print(f"[{src}] {content_str}...")
