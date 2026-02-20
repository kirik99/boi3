/**
 * Упрощённый сервер для локального запуска
 * Обходит проблемы с сокетами в Node.js v24
 */

import express from 'express';
import multer from 'multer';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import fetch from 'node-fetch';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 5000;

// API конфигурация
const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY || 'your-api-key-here';
const OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions';

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Статика для клиента
app.use(express.static(path.join(__dirname, 'client')));
app.use('/uploads', express.static(path.join(__dirname, 'client', 'public', 'uploads')));

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

// Простое хранилище в памяти (для локального теста)
const conversations = new Map();
const messages = new Map();
let conversationIdCounter = 1;

// API маршруты

// Загрузка изображений
app.post('/api/upload', upload.single('image'), (req, res) => {
    if (!req.file) {
        return res.status(400).json({ message: 'No file uploaded' });
    }
    const imageUrl = `/uploads/${req.file.filename}`;
    res.status(201).json({ url: imageUrl });
});

// Получить все беседы
app.get('/api/conversations', (req, res) => {
    const convs = Array.from(conversations.values());
    res.json(convs);
});

// Создать беседу
app.post('/api/conversations', (req, res) => {
    const { title } = req.body;
    const id = conversationIdCounter++;
    const conversation = { id, title: title || 'New Chat', createdAt: new Date().toISOString() };
    conversations.set(id, conversation);
    messages.set(id, []);
    res.status(201).json(conversation);
});

// Получить беседу с сообщениями
app.get('/api/conversations/:id', (req, res) => {
    const id = parseInt(req.params.id);
    const conversation = conversations.get(id);
    if (!conversation) {
        return res.status(404).json({ message: 'Conversation not found' });
    }
    const convMessages = messages.get(id) || [];
    res.json({ ...conversation, messages: convMessages });
});

// Удалить беседу
app.delete('/api/conversations/:id', (req, res) => {
    const id = parseInt(req.params.id);
    conversations.delete(id);
    messages.delete(id);
    res.status(204).send();
});

// Отправить сообщение
app.post('/api/conversations/:id/messages', async (req, res) => {
    try {
        const conversationId = parseInt(req.params.id);
        const { content, imageUrl } = req.body;

        // Сохраняем сообщение пользователя
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

        // Подготовка запроса к API
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

        // Добавляем историю сообщений
        for (const msg of convMessages) {
            if (msg.role === 'user' && msg.imageUrl) {
                const base64Image = imageUrl.startsWith('http') 
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

        // Запрос к OpenRouter
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

        // Сохраняем ответ ассистента
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

// Catch-all для SPA (Express 5 использует другой синтаксис)
app.get('/*path', (req, res) => {
    res.sendFile(path.join(__dirname, 'client', 'index.html'));
});

// Запуск сервера
app.listen(PORT, () => {
    console.log(`\n🚀 Мультимодальный AI-агент запущен!`);
    console.log(`📍 Откройте в браузере: http://localhost:${PORT}`);
    console.log(`\n💡 Бесплатная модель: arcee-ai/trinity-large-preview:free`);
    console.log(`🔑 API ключ настроен\n`);
});