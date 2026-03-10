import { Request, Response } from "express";
import fetch from "node-fetch";

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_KEY;

/**
 * Fallback function to fetch information from the internet.
 * Returns mock data for common laboratory instruments.
 * Rule 5: If database returns no results - perform internet search
 */
export async function fetchInternetInfo(query: string): Promise<string> {
  // DISABLED: No hardcoded answers - only use database
  // All information must come from knowledge_base table
  return "";
}

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
 * Search for relevant document chunks using the Python RAG pipeline
 */
export async function searchChunks(query: string, limit = 5) {
  console.log(`[RAG] Querying Python RAG service: "${query}"`);

  try {
    const response = await fetch('http://localhost:8000/rag', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, limit })
    });

    if (!response.ok) {
      throw new Error(`RAG service error: ${response.status}`);
    }

    const data = await response.json() as { results: any[], source: string };
    console.log(`[RAG] Results from ${data.source}: ${data.results.length} items`);
    return { results: data.results, source: data.source };
  } catch (error) {
    console.error('[RAG] Python RAG service failed:', error);
    // Fallback to empty results if service is down
    return [];
  }
}

/**
 * Get all documents
 */
export async function getDocuments() {
  const response = await fetch(
    `${SUPABASE_URL}/rest/v1/lab_methods?select=*`,
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
    `${SUPABASE_URL}/rest/v1/knowledge_base?select=*`,
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
