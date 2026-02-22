import { Request, Response } from "express";
import fetch from "node-fetch";

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_KEY;

/**
 * Get embedding from local embedding server
 */
async function getEmbedding(text: string): Promise<number[]> {
  try {
    const response = await fetch('http://localhost:8000/embed', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });

    if (!response.ok) {
      throw new Error(`Embedding server error: ${response.status}`);
    }

    const data = await response.json() as { embedding: number[] };
    return data.embedding;
  } catch (error) {
    console.error('Embedding error:', error);
    throw error;
  }
}

/**
 * Search for relevant document chunks using vector or text search
 */
export async function searchChunks(query: string, limit = 5) {
  const supabaseUrl = SUPABASE_URL;
  const supabaseKey = SUPABASE_KEY;

  console.log(`[RAG] Searching for: "${query}"`);

  try {
    // 1. Try Vector Search first
    const embedding = await getEmbedding(query);

    // Using Supabase RPC for vector search
    // Note: requires 'match_chunks' function to be defined in Supabase
    const rpcResponse = await fetch(`${supabaseUrl}/rest/v1/rpc/match_chunks`, {
      method: 'POST',
      headers: {
        'apikey': supabaseKey!,
        'Authorization': `Bearer ${supabaseKey!}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query_embedding: embedding,
        match_count: limit
      })
    });

    if (rpcResponse.ok) {
      const results = await rpcResponse.json();
      if (Array.isArray(results) && results.length > 0) {
        console.log(`[RAG] Vector search found ${results.length} results`);
        return results;
      }
    } else {
      const err = await rpcResponse.text();
      console.warn(`[RAG] Vector RPC failed: ${rpcResponse.status} ${err}`);
    }
  } catch (error) {
    console.warn('[RAG] Vector search failed, falling back to text search:', error);
  }

  // 2. Fallback: Text search on document_chunks
  const queryLower = query.toLowerCase();

  try {
    const response = await fetch(`${supabaseUrl}/rest/v1/document_chunks?select=*`, {
      headers: {
        'apikey': supabaseKey!,
        'Authorization': `Bearer ${supabaseKey!}`,
        'Accept': 'application/json'
      }
    });

    if (response.ok) {
      const allChunks = await response.json() as any[];
      const results = allChunks.filter(chunk =>
        chunk.content?.toLowerCase().includes(queryLower)
      ).slice(0, limit);

      if (results.length > 0) {
        console.log(`[RAG] Text search (chunks) found ${results.length} results`);
        return results;
      }
    }
  } catch (error) {
    console.error('[RAG] Text search (chunks) failed:', error);
  }

  // 3. Last resort: Search the main 'documents' table
  console.log(`[RAG] No chunks found, trying 'documents' table...`);
  try {
    const response = await fetch(`${supabaseUrl}/rest/v1/documents?select=*`, {
      headers: {
        'apikey': supabaseKey!,
        'Authorization': `Bearer ${supabaseKey!}`,
        'Accept': 'application/json'
      }
    });

    if (response.ok) {
      const allDocs = await response.json() as any[];
      const results = allDocs.filter(doc =>
        doc.title?.toLowerCase().includes(queryLower) ||
        doc.full_text?.toLowerCase().includes(queryLower)
      ).slice(0, limit).map(doc => ({
        content: `Document: ${doc.title}\nContent: ${doc.full_text || doc.content || ""}`
      }));

      console.log(`[RAG] Text search (documents) found ${results.length} results`);
      return results;
    }
  } catch (error) {
    console.error('[RAG] Text search (documents) failed:', error);
  }

  return [];
}

/**
 * Get all documents
 */
export async function getDocuments() {
  const response = await fetch(
    `${SUPABASE_URL}/rest/v1/documents?select=*`,
    {
      headers: {
        'apikey': SUPABASE_KEY!,
        'Authorization': `Bearer ${SUPABASE_KEY!}`
      }
    }
  );

  if (!response.ok) {
    throw new Error(`Supabase error: ${response.status}`);
  }

  return await response.json();
}

/**
 * Get all document chunks
 */
export async function getChunks() {
  const response = await fetch(
    `${SUPABASE_URL}/rest/v1/document_chunks?select=*`,
    {
      headers: {
        'apikey': SUPABASE_KEY!,
        'Authorization': `Bearer ${SUPABASE_KEY!}`
      }
    }
  );

  if (!response.ok) {
    throw new Error(`Supabase error: ${response.status}`);
  }

  return await response.json();
}

/**
 * RAG Search endpoint
 */
export async function ragSearch(req: Request, res: Response) {
  try {
    const { query, limit = 5 } = req.body;

    if (!query) {
      return res.status(400).json({ message: "Query is required" });
    }

    const results = await searchChunks(query, limit);
    res.json({ results, query });
  } catch (error: any) {
    console.error('RAG search error:', error);
    res.status(500).json({ message: error.message });
  }
}

/**
 * Get documents endpoint
 */
export async function listDocuments(_req: Request, res: Response) {
  try {
    const documents = await getDocuments();
    res.json(documents);
  } catch (error: any) {
    console.error('Documents error:', error);
    res.status(500).json({ message: error.message });
  }
}

/**
 * Get chunks endpoint
 */
export async function listChunks(_req: Request, res: Response) {
  try {
    const chunks = await getChunks();
    res.json(chunks);
  } catch (error: any) {
    console.error('Chunks error:', error);
    res.status(500).json({ message: error.message });
  }
}
