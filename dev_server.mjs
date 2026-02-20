/**
 * Сервер для локальной разработки с Vite
 */

import { createServer } from 'vite';
import express from 'express';
import { createServer as createHttpServer } from 'http';
import multer from 'multer';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import fetch from 'node-fetch';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = process.env.PORT || 5000;

// API конфигурация
const OPENROUTER_API_KEY = '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';
const OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions';

// Express для API
const app = express();
const httpServer = createHttpServer(app);

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Настройка загрузки файлов
const uploadDir = path.join(__dirname, 'client', 'public', 'uploads');
if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir, { recursive: true });
}

const storage = multer.diskStorage({
    destination: (req, file, cb) => cb(null, uploadDir),
    filename: (req, file, cb) => {
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1e9);
        cb(null, uniqueSuffix + path.extname(file.originalname));
    }
});

const upload = multer({ storage });

// Простое хранилище в памяти
const conversations = new Map();
const messages = new Map();
let conversationIdCounter = 1;

// API маршруты
app.post('/api/upload', upload.single('image'), (req, res) => {
    if (!req.file) {
        return res.status(400).json({ message: 'No file uploaded' });
    }
    const imageUrl = `/uploads/${req.file.filename}`;
    res.status(201).json({ url: imageUrl });
});

app.get('/api/conversations', (req, res) => {
    res.json(Array.from(conversations.values()));
});

app.post('/api/conversations', (req, res) => {
    const { title } = req.body;
    const id = conversationIdCounter++;
    const conversation = { id, title: title || 'New Chat', createdAt: new Date().toISOString() };
    conversations.set(id, conversation);
    messages.set(id, []);
    res.status(201).json(conversation);
});

app.get('/api/conversations/:id', (req, res) => {
    const id = parseInt(req.params.id);
    const conversation = conversations.get(id);
    if (!conversation) {
        return res.status(404).json({ message: 'Conversation not found' });
    }
    const convMessages = messages.get(id) || [];
    res.json({ ...conversation, messages: convMessages });
});

app.delete('/api/conversations/:id', (req, res) => {
    const id = parseInt(req.params.id);
    conversations.delete(id);
    messages.delete(id);
    res.status(204).send();
});

app.post('/api/conversations/:id/messages', async (req, res) => {
    try {
        const conversationId = parseInt(req.params.id);
        const { content, imageUrl } = req.body;

        const userMessage = {
            id: Date.now(),
            conversationId,
            role: 'user',
            content,
            imageUrl,
            createdAt: new Date().toISOString()
        };
        
        const convMessages = messages.get(conversationId) || [];
        convMessages.push(userMessage);
        messages.set(conversationId, convMessages);

        const apiMessages = [
            {
                role: 'system',
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

Always follow this structure precisely.`
            }
        ];

        for (const msg of convMessages) {
            if (msg.role === 'user' && msg.imageUrl) {
                const base64Image = imageUrl?.startsWith('http') 
                    ? msg.imageUrl 
                    : `data:image/jpeg;base64,${fs.readFileSync(path.join(__dirname, 'client', 'public', msg.imageUrl)).toString('base64')}`;
                apiMessages.push({
                    role: 'user',
                    content: [
                        { type: 'text', text: msg.content },
                        { type: 'image_url', image_url: { url: base64Image } }
                    ]
                });
            } else {
                apiMessages.push({
                    role: msg.role,
                    content: msg.content
                });
            }
        }

        const response = await fetch(OPENROUTER_URL, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model: 'arcee-ai/trinity-large-preview:free',
                messages: apiMessages,
                stream: false
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: { message: response.statusText } }));
            throw new Error(`API Error: ${response.status} - ${errorData.error?.message || 'Unknown error'}`);
        }

        const data = await response.json();
        const assistantContent = data.choices[0].message.content;

        const assistantMessage = {
            id: Date.now() + 1,
            conversationId,
            role: 'assistant',
            content: assistantContent,
            createdAt: new Date().toISOString()
        };
        convMessages.push(assistantMessage);
        messages.set(conversationId, convMessages);

        res.json({ content: assistantContent });

    } catch (error) {
        console.error('Error:', error);
        res.status(500).json({ message: error.message });
    }
});

// Запускаем Vite dev server
async function start() {
    // Vite для клиента
    const vite = await createServer({
        configFile: path.join(__dirname, 'vite.config.ts'),
        root: path.join(__dirname, 'client'),
        server: {
            middlewareMode: true,
            hmr: { port: 5173 }
        },
        appType: 'spa'
    });

    app.use(vite.middlewares);

    httpServer.listen(PORT, () => {
        console.log(`\n🚀 Мультимодальный AI-агент запущен!`);
        console.log(`📍 Откройте в браузере: http://localhost:${PORT}`);
        console.log(`\n💡 Бесплатная модель: arcee-ai/trinity-large-preview:free`);
        console.log(`🔑 API ключ настроен\n`);
    });
}

start().catch(console.error);