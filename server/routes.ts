
import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import multer from "multer";
import path from "path";
import fs from "fs";
import express from "express";
import OpenAI from "openai";

// Configure OpenAI
const openai = new OpenAI({
  apiKey: process.env.AI_INTEGRATIONS_OPENAI_API_KEY,
  baseURL: process.env.AI_INTEGRATIONS_OPENAI_BASE_URL,
});

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
  // Serve uploaded files statically - handled by Vite in dev or static middleware in prod?
  // client/public is served at root.

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

      // 1. Save User Message
      const userMessage = await storage.createMessage({
        conversationId,
        role: "user",
        content,
        imageUrl,
      });

      // 2. Prepare context for OpenAI
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

      // System prompt
      const systemMessage = {
        role: "system",
        content: `You are a multimodal AI agent. 
Tasks:
1. Analyze text and images.
2. If image present, describe it or answer questions about it.
3. If text only, answer text.
4. Output structured, helpful responses.
Format:
Answer: <clear explanation>
If image analyzed:
Found on image:
- ...
Agent actions:
- received request
- analyzed input
- generated response`,
      };

      // Set headers for SSE
      res.setHeader("Content-Type", "text/event-stream");
      res.setHeader("Cache-Control", "no-cache");
      res.setHeader("Connection", "keep-alive");

      // 3. Call OpenAI with streaming
      const stream = await openai.chat.completions.create({
        model: "gpt-5.2",
        messages: [systemMessage, ...apiMessages] as any,
        max_completion_tokens: 1000,
        stream: true,
      });

      let assistantContent = "";

      for await (const chunk of stream) {
        const content = chunk.choices[0]?.delta?.content || "";
        if (content) {
          assistantContent += content;
          res.write(`data: ${JSON.stringify({ content })}\n\n`);
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
      console.error("OpenAI Error:", error);
      if (!res.headersSent) {
        res.status(500).json({ message: error.message || "Internal Server Error" });
      } else {
        res.write(`data: ${JSON.stringify({ error: error.message })}\n\n`);
        res.end();
      }
    }
  });

  return httpServer;
}
