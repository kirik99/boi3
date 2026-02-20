# Мультимодальный AI-агент

AI-агент с поддержкой текста, изображений и векторного поиска по базе знаний.

## Особенности

- 📝 **Текст и изображения** — мультимодальные запросы
- 🧠 **LLM через OpenRouter** — `arcee-ai/trinity-large-preview:free` (бесплатно)
- 🔍 **Векторный поиск** — RAG через Supabase + Hugging Face embeddings
- 💾 **База знаний** — документы лабораторных методик и протоколов
- 📡 **Streaming** — потоковая передача ответов
- 🛡️ **Обработка ошибок** — graceful fallbacks

## Быстрый старт

### 1. Установка зависимостей

```bash
# Node.js
npm install

# Python (для эмбеддингов)
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Создайте `.env.secrets` (см. `.env.secrets.example`):

```
OPENROUTER_API_KEY=sk-or-v1-your_key
SUPABASE_KEY=your_supabase_key
HF_TOKEN=hf_your_token
```

### 3. Настройка Supabase (векторный поиск)

В Supabase SQL Editor выполните:

```sql
create extension if not exists vector;
alter table documents add column if not exists embedding vector(384);
create index documents_embedding_idx on documents using ivfflat (embedding vector_cosine_ops);
```

### 4. Тестовые данные (опционально)

```bash
python seed_data.py
```

### 5. Запуск

```bash
npm run dev
```

Приложение: http://localhost:5000

---

## Документация

| Файл | Описание |
|------|----------|
| [TEAM_SETUP.md](./TEAM_SETUP.md) | Полная инструкция для команды |
| [.env.secrets.example](./.env.secrets.example) | Шаблон переменных окружения |

## Структура

```
├── client/           # React + Vite frontend
├── server/           # Node.js backend
├── shared/           # Общие типы и схемы
├── embedding.py      # Hugging Face embeddings API
├── supabase_client.py # Supabase клиент
├── seed_data.py      # Скрипт заполнения БД
└── requirements.txt  # Python зависимости
```

## API Ключи

| Сервис | Получение | Стоимость |
|--------|-----------|-----------|
| OpenRouter | https://openrouter.ai/keys | $0 (free model) |
| Hugging Face | https://huggingface.co/tokens | $0.10/мес бесплатно |
| Supabase | Project Settings → API | Free tier |

## Лицензия

MIT