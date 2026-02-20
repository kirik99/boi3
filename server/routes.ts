
import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import multer from "multer";
import path from "path";
import fs from "fs";
import express from "express";
import { ragSearch, listDocuments, listChunks } from "./rag";

// Configure OpenRouter
const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY;
const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";

// Configure Multer for file uploads
const uploadDir = path.join(process.cwd(), "client", "public", "uploads");
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

const storageConfig = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, uploadDir);
  },
  filename: function (req, file, cb) {
    const uniqueSuffix = Date.now() + "-" + Math.round(Math.random() * 1e9);
    cb(null, uniqueSuffix + path.extname(file.originalname));
  },
});

const upload = multer({ storage: storageConfig });

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  // RAG: Search document chunks
  app.post("/api/search", ragSearch);
  
  // RAG: Get all documents
  app.get("/api/documents", listDocuments);
  
  // RAG: Get all chunks
  app.get("/api/chunks", listChunks);

  app.post("/api/upload", upload.single("image"), (req, res) => {
    if (!req.file) {
      return res.status(400).json({ message: "No file uploaded" });
    }
    const imageUrl = `/uploads/${req.file.filename}`;
    res.status(201).json({ url: imageUrl });
  });

  // Conversations API
  app.get("/api/conversations", async (req, res) => {
    const conversations = await storage.getConversations();
    res.json(conversations);
  });

  app.get("/api/conversations/:id", async (req, res) => {
    const id = parseInt(req.params.id);
    const conversation = await storage.getConversation(id);
    if (!conversation) {
      return res.status(404).json({ message: "Conversation not found" });
    }
    const messages = await storage.getMessages(id);
    res.json({ ...conversation, messages });
  });

  app.post("/api/conversations", async (req, res) => {
    const { title } = req.body;
    const conversation = await storage.createConversation(title || "New Chat");
    res.status(201).json(conversation);
  });

  app.delete("/api/conversations/:id", async (req, res) => {
    const id = parseInt(req.params.id);
    await storage.deleteConversation(id);
    res.status(204).send();
  });

  // Messages API
  app.post("/api/conversations/:id/messages", async (req, res) => {
    try {
      const conversationId = parseInt(req.params.id);
      const { content, imageUrl } = req.body;

      if (!OPENROUTER_API_KEY) {
        return res.status(500).json({ message: "OPENROUTER_API_KEY is not configured" });
      }

      // 1. Save User Message
      await storage.createMessage({
        conversationId,
        role: "user",
        content,
        imageUrl,
      });

      // 2. Prepare context for OpenRouter
      const history = await storage.getMessages(conversationId);

      const apiMessages = history.map((msg) => {
        if (msg.role === "user" && msg.imageUrl) {
          return {
            role: "user",
            content: [
              { type: "text", text: msg.content },
              {
                type: "image_url",
                image_url: {
                  url: msg.imageUrl.startsWith("http")
                    ? msg.imageUrl
                    : `data:image/jpeg;base64,${fs.readFileSync(path.join(process.cwd(), "client", "public", msg.imageUrl)).toString("base64")}`
                },
              },
            ],
          };
        } else {
          return {
            role: msg.role as "user" | "assistant",
            content: msg.content,
          };
        }
      });

      const systemMessage = {
        role: "system",
        content: `You are a multimodal AI agent. Follow this exact format for all responses:

Answer:
<clear explanation of the result>

If image analysis was performed:
What was found on the image:
- ...

Agent actions:
- sent request to API
- received response
- formed final result

Always follow this structure precisely.`,
      };

      // Set headers for SSE
      res.setHeader("Content-Type", "text/event-stream");
      res.setHeader("Cache-Control", "no-cache");
      res.setHeader("Connection", "keep-alive");

      // 3. Call OpenRouter with streaming
      const response = await fetch(OPENROUTER_URL, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${OPENROUTER_API_KEY}`,
          "Content-Type": "application/json",
          "HTTP-Referer": "https://replit.com", // Optional, for OpenRouter rankings
          "X-Title": "Replit Multi-modal Agent", // Optional
        },
        body: JSON.stringify({
          model: "arcee-ai/trinity-large-preview:free", // Free model
          messages: [systemMessage, ...apiMessages],
          stream: true,
        }),
      });

      if (!response.ok) {
        const error = await response.text();
        // Check if it's an API limit error
        if (response.status === 429) {
          throw new Error(`API rate limit exceeded. Please try again later.`);
        } else if (response.status === 401) {
          throw new Error(`Invalid API key. Please check your OpenRouter API key configuration.`);
        } else if (response.status === 402) {
          throw new Error(`Payment required. Your OpenRouter account may have exceeded usage limits.`);
        } else {
          throw new Error(`OpenRouter Error: ${response.status} - ${error}`);
        }
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let assistantContent = "";

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const dataStr = line.slice(6).trim();
              if (dataStr === "[DONE]") continue;

              try {
                const data = JSON.parse(dataStr);
                const content = data.choices[0]?.delta?.content || "";
                if (content) {
                  assistantContent += content;
                  res.write(`data: ${JSON.stringify({ content })}\n\n`);
                }
              } catch (e) {
                // Ignore parse errors for incomplete lines
              }
            }
          }
        }
      }

      // 4. Save Assistant Message
      await storage.createMessage({
        conversationId,
        role: "assistant",
        content: assistantContent,
      });

      res.write(`data: ${JSON.stringify({ done: true })}\n\n`);
      res.end();

    } catch (error: any) {
      console.error("Agent Error:", error);
      
      // Handle specific API limit errors
      if (error.message.includes('rate limit') || error.message.includes('exceeded usage')) {
        const errorMessage = {
          role: "assistant",
          content: `Answer:
I apologize, but I've reached my API usage limits. Please check your OpenRouter account for available quota or try again later.

Agent actions:
- attempted to send request to API
- encountered API limit error
- formed final result with error information`
        };
        
        // Save the error message to the conversation
        try {
          await storage.createMessage({
            conversationId: parseInt(req.params.id),
            role: "assistant",
            content: errorMessage.content,
          });
        } catch (storageError) {
          console.error("Failed to save error message to storage:", storageError);
        }
        
        if (!res.headersSent) {
          res.status(200).json({ message: error.message });
        } else {
          res.write(`data: ${JSON.stringify({ error: error.message })}\n\n`);
          res.end();
        }
      } else {
        if (!res.headersSent) {
          res.status(500).json({ message: error.message || "Internal Server Error" });
        } else {
          res.write(`data: ${JSON.stringify({ error: error.message })}\n\n`);
          res.end();
        }
      }
    }
  });

  return httpServer;
}
