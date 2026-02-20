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
 * Search for relevant document chunks using text search
 */
export async function searchChunks(query: string, limit = 5) {
  const supabaseUrl = SUPABASE_URL;
  const supabaseKey = SUPABASE_KEY;
  
  // Get all chunks and filter locally
  const url = `${supabaseUrl}/rest/v1/document_chunks?select=*`;
  
  const response = await fetch(url, {
    headers: {
      'apikey': supabaseKey!,
      'Authorization': `Bearer ${supabaseKey!}`,
      'Accept': 'application/json'
    }
  });
  
  if (!response.ok) {
    throw new Error(`Supabase error: ${response.status}`);
  }
  
  const allChunks = await response.json() as any[];
  
  // Local text search (case insensitive)
  const queryLower = query.toLowerCase();
  const results = allChunks.filter(chunk => 
    chunk.content?.toLowerCase().includes(queryLower)
  ).slice(0, limit);
  
  return results;
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
