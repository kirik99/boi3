import os
import requests
import logging
from supabase import create_client
from dotenv import load_dotenv
from embedding import get_embedding

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("SUPABASE_URL or SUPABASE_KEY not found in .env")
    raise ValueError("Missing Supabase credentials")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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
        # Extract keywords (words > 3 chars)
        keywords = [w.strip(",.!?") for w in query.split() if len(w) > 3]
        if keywords:
            try:
                # Build OR filter for keywords
                filter_str = " or ".join([f"method_name.ilike.%{k}%" for k in keywords])
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

def retrieve_from_knowledge_base(query, query_embedding, match_threshold=0.15, match_count=5):
    """Step 2: Vector Search in knowledge_base with text fallback."""
    logger.info("🔍 Searching in 'knowledge_base'...")
    results = []
    try:
        rpc_res = supabase.rpc("match_chunks", {
            "query_embedding": query_embedding,
            "match_threshold": match_threshold,
            "match_count": match_count
        }).execute()
        
        if rpc_res.data:
            logger.info(f"✅ Found {len(rpc_res.data)} matches in 'knowledge_base'")
            results.extend([{
                "content": r.get("content"),
                "source": r.get("file_source", "Unknown"),
                "similarity": r.get("similarity")
            } for r in rpc_res.data])
    except Exception as e:
        logger.error(f"❌ Error in match_chunks: {e}")
    
    # Text-based fallback for chunks
    if not results:
        logger.info("🔍 Keyword searching in 'knowledge_base'...")
        # Look for equipment-related keywords if not found
        important_words = ["оборудование", "прибор", "список", "инструкция", "метод"]
        query_words = [w.strip(",.!?").lower() for w in query.split() if len(w) > 3]
        
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
                # Generic text search
                filter_str = " or ".join([f"content.ilike.%{k}%" for k in query_words[:3]])
                if filter_str:
                    text_res = supabase.table("knowledge_base").select("*").or_(filter_str).limit(match_count).execute()
                    if text_res.data:
                        results.extend([{
                            "content": r.get("content"),
                            "source": r.get("file_source", "Unknown") + " (text search)",
                            "similarity": 0.5
                        } for r in text_res.data])
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
    """Main RAG Pipeline."""
    logger.info(f"🚀 Processing RAG query: {query}")
    
    # Check if user explicitly asks for internet
    force_internet = any(word in query.lower() for word in ["интернет", "сеть", "internet", "web"])
    
    # Get embedding
    embedding = get_embedding(query)
    if not embedding:
        logger.warning("⚠️ Failed to generate embedding.")
        return {"results": [], "source": "None"}

    all_results = []
    found_locally = False

    # 1. High Priority: Lab Methods
    results = retrieve_from_lab_methods(query, embedding)
    if results:
        all_results.extend(results)
        found_locally = True
    
    # 2. Vector Search: Knowledge Base
    results = retrieve_from_knowledge_base(query, embedding)
    if results:
        all_results.extend(results)
        found_locally = True
    
    # 3. Fallback: Internet (only if nothing local or user explicitly asked)
    if not found_locally or force_internet:
        internet_results = internet_search_fallback(query)
        all_results.extend(internet_results)
        return {"results": all_results, "source": "mixed" if found_locally else "internet"}
    
    return {"results": all_results, "source": "database"}

if __name__ == "__main__":
    # Test
    test_q = "какое оборудование есть в лаборатории"
    response: dict = rag_query(test_q)
    print(f"\nFinal Response for '{test_q}' (Source: {response.get('source')}):")
    results = response.get('results', [])
    for r in results:
        # Use explicit dict access to avoid lint issues
        if isinstance(r, dict):
            src = r.get('source', 'Unknown')
            cnt = r.get('content', '')
            print(f"[{src}] {str(cnt)[:100]}...")
