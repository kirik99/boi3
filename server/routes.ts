import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import multer from "multer";
import path from "path";
import fs from "fs";
import express from "express";
import { ragSearch, listDocuments, listChunks, searchChunks } from "./rag";
import { 
  hasInstrumentMention, 
  extractInstrumentNames, 
  hasMultipleModels, 
  buildClarificationPrompt,
  buildModelClarificationPrompt,
  buildInstrumentResponse,
  isRussian
} from "./promptRules";

// Configure DeepSeek
const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY?.trim();
const DEEPSEEK_URL = "https://api.deepseek.com/chat/completions";

// Configure Supabase
const SUPABASE_URL = process.env.SUPABASE_URL || "https://inlnzpjewdyovotnidsy.supabase.co";
const SUPABASE_KEY = process.env.SUPABASE_KEY;

if (!SUPABASE_KEY) {
  console.warn("SUPABASE_KEY is not defined in environment variables!");
}

if (DEEPSEEK_API_KEY) {
  console.log(`[DeepSeek] API Key loaded (length: ${DEEPSEEK_API_KEY.length})`);
} else {
  console.warn("[DeepSeek] API Key is NOT configured in environment");
}

// Configure Multer for file uploads
const uploadDir = path.join(process.cwd(), "client", "public", "uploads");
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

const storageConfig = multer.diskStorage({
  destination: function (req: any, file: any, cb: any) {
    cb(null, uploadDir);
  },
  filename: function (req: any, file: any, cb: any) {
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

  app.post("/api/upload", upload.single("image") as any, (req: any, res) => {
    if (!(req as any).file) {
      return res.status(400).json({ message: "No file uploaded" });
    }
    const imageUrl = `/uploads/${(req as any).file.filename}`;
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

  // Messages API - with STRICT PROMPT RULES
  app.post("/api/conversations/:id/messages", async (req, res) => {
    try {
      const conversationId = parseInt(req.params.id);
      const { content, imageUrl } = req.body;

      if (!DEEPSEEK_API_KEY) {
        return res.status(500).json({ message: "DEEPSEEK_API_KEY is not configured" });
      }

      // === RULE 1: Check if instrument is mentioned (RELAXED) ===
      // Even if instrument is not mentioned, we proceed to RAG to see if we can find something.
      // We only log it for now.
      if (!hasInstrumentMention(content)) {
        console.log(`[Prompt Rules] No explicit instrument mentioned, proceeding to general RAG.`);
      }

      // === Extract instrument names (normalizes test-machine variants) ===
      const instruments = extractInstrumentNames(content);
      
      // === RULE 7: If multiple models detected - ask for clarification (RELAXED) ===
      // Only ask if it's very ambiguous, otherwise proceed.
      if (hasMultipleModels(instruments) && instruments.length > 3) {
        await storage.createMessage({
          conversationId,
          role: "user",
          content,
          imageUrl,
        });
        
        const modelClarificationResponse = buildModelClarificationPrompt(instruments);
        await storage.createMessage({
          conversationId,
          role: "assistant",
          content: modelClarificationResponse,
        });
        
        console.log(`[Prompt Rules] Too many models detected: ${instruments.join(', ')}`);
        res.json({ content: modelClarificationResponse });
        return;
      }

      // 1. Save User Message
      await storage.createMessage({
        conversationId,
        role: "user",
        content,
        imageUrl,
      });

      // 2. Prepare context for DeepSeek
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

      // 3. RAG: Search for relevant context using the unified Python RAG service
      let context = "";
      let foundInDatabase = false;
      let fromInternet = false;
      
      try {
        const ragResponse = await searchChunks(content) as { results: any[], source: string };
        if (ragResponse && ragResponse.results.length > 0) {
          const results = ragResponse.results;
          foundInDatabase = ragResponse.source === "database" || ragResponse.source === "lab_methods" || ragResponse.source === "knowledge_base" || ragResponse.source === "mixed";
          fromInternet = ragResponse.source === "internet" || ragResponse.source === "mixed";
          
          context = "\n\nRelevant information from our " + (fromInternet ? "sources (including internet)" : "laboratory database") + ":\n" + 
            results.map((r: any) => `[Source: ${r.source}] ${r.content}`).join("\n\n---\n\n");
        }
      } catch (error) {
        console.error("RAG search failed:", error);
      }
      // === RULE 3: Build answer with strict structure only if methodology requested ===
      const instrumentName = instruments.length > 0 ? instruments[0] : "Не указан";
      const isMethodologyRequest = ['методика', 'инструкция', 'калибровка', 'как работать', 'измерение', 'method', 'instruction', 'calibration'].some(word => content.toLowerCase().includes(word));
      
      let formattedResponse = "";
      
      if (instrumentName !== "Не указан" || isMethodologyRequest) {
          // Extract sections from context
          const calibrationMatch = context.match(/(?:Калибровка[^:]*:|Calibration[^:]*:|Приготовление\s+\w+[^.\n]*\.)([\s\S]*?)(?:Измерение|Методика|Measurement|Methodology|Образец|$)/i);
          const methodologyMatch = context.match(/(?:Измерение\s+\w*[^.\n]*[:\.]?|Методика[^:]*:|Measurement[^:]*:|Methodology[^:]*:)([\s\S]*?)(?:Прибор|Калибровка|Calibration|Приготовление|$)/i);
          
          const calibration = calibrationMatch ? calibrationMatch[1].trim() : null;
          const methodology = methodologyMatch ? methodologyMatch[1].trim() : null;

          // Build strict formatted response
          let finalCalibration = calibration;
          let finalMethodology = methodology;
          
          if (!calibration && !methodology && context) {
            const parts = context.split('---');
            if (parts.length > 0) {
              finalCalibration = parts[0].trim().substring(0, 500);
              finalMethodology = parts.length > 1 ? parts.slice(1).join('\n\n').trim() : parts[0].trim().substring(500);
            }
          }
          
          formattedResponse = buildInstrumentResponse(
            instrumentName,
            finalCalibration,
            finalMethodology,
            fromInternet,
            !foundInDatabase && !fromInternet
          );
      } else {
          // For general questions, provide a more natural conversational context
          formattedResponse = "Вы — универсальный лабораторный помощник. Используйте предоставленные данные для ответа на общий вопрос пользователя.";
      }

      let systemContent = `Вы — профессиональный лабораторный ассистент. Отвечайте ВСЕГДА на русском языке.\n\n`;
      
      // === RULE 4: Explicit Source Labeling ===
      if (fromInternet) {
        if (foundInDatabase) {
            systemContent += `⚠️ ВНИМАНИЕ: Для части вашего вопроса информация в локальной базе не найдена, поэтому я дополнительно поискал в интернете.\n\n`;
        } else {
            systemContent += `⚠️ ВНИМАНИЕ: Информация не найдена в нашей базе приборов. Я нашел следующие данные в открытых источниках (интернет):\n\n`;
        }
      } else if (foundInDatabase) {
        systemContent += `✅ Информация получена из официальной базы данных нашей лаборатории.\n\n`;
      }
      
      systemContent += formattedResponse;

      // === RULE 6: Source Transparency ===
      if (context) {
        systemContent += `\n\n[ДАННЫЕ ИЗ БАЗЫ/ИНТЕРНЕТА ДЛЯ АНАЛИЗА]:\n${context}`;
      }

      // Explicit instruction to LLM about source mentioning
      systemContent += `\n\nПри ответе обязательно укажи, если информация взята из интернета. Если информация взята из нашей базы, отвечай уверенно как ассистент нашей лаборатории.`;

      console.log(`[Chat] Instrument: ${instrumentName}`);
      console.log(`[Chat] Found in Database: ${foundInDatabase}`);
      // fromInternet logging removed
      console.log(`[Chat] Russian query: ${isRussian(content)}`);

      const model = "deepseek-chat";
      const finalMessages = [...apiMessages];

      // Gemma 3 hack: move system instructions to THE LAST user message
      if (model.includes("gemma") && finalMessages.length > 0) {
        const lastMsg = finalMessages[finalMessages.length - 1];
        console.log(`[Chat] Applying Gemma 3 system prompt workaround`);
        if (typeof lastMsg.content === "string") {
          lastMsg.content = `[SYSTEM INSTRUCTIONS]\n${systemContent}\n\n[USER QUESTION]:\n${lastMsg.content}`;
        } else if (Array.isArray(lastMsg.content)) {
          lastMsg.content.unshift({ type: "text", text: `[SYSTEM INSTRUCTIONS]\n${systemContent}\n\n[USER QUESTION]:\n` });
        }
      } else {
        finalMessages.unshift({ role: "system", content: systemContent } as any);
      }

      // Set headers for SSE
      res.setHeader("Content-Type", "text/event-stream");
      res.setHeader("Cache-Control", "no-cache");
      res.setHeader("Connection", "keep-alive");

      // 4. Call DeepSeek with streaming
      const response = await fetch(DEEPSEEK_URL, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${DEEPSEEK_API_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model,
          messages: finalMessages as any[],
          stream: true,
        }),
      });

      if (!response.ok) {
        const error = await response.text();
        if (response.status === 429) {
          throw new Error(`API rate limit exceeded. Please try again later.`);
        } else if (response.status === 401) {
          throw new Error(`Invalid API key.`);
        } else if (response.status === 402) {
          throw new Error(`Payment required.`);
        } else {
          throw new Error(`DeepSeek Error: ${response.status} - ${error}`);
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
                // Ignore parse errors
              }
            }
          }
        }
      }

      // 5. Save Assistant Message
      await storage.createMessage({
        conversationId,
        role: "assistant",
        content: assistantContent,
      });

      res.write(`data: ${JSON.stringify({ done: true })}\n\n`);
      res.end();

    } catch (error: any) {
      console.error("Agent Error:", error);

      if (error.message.includes('rate limit') || error.message.includes('exceeded usage')) {
        const errorMessage = {
          role: "assistant",
          content: `Извините, достигнут лимит использования API. Пожалуйста, проверьте квоту DeepSeek или попробуйте позже.`
        };

        try {
          await storage.createMessage({
            conversationId: parseInt(req.params.id),
            role: "assistant",
            content: errorMessage.content,
          });
        } catch (storageError) {
          console.error("Failed to save error message:", storageError);
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
