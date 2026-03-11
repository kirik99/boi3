# Laboratory AI Assistant (MML Agent)

AI-ассистент для лаборатории с поддержкой текста, изображений и интеллектуального поиска по базе знаний (RAG).

## Особенности

- 🔬 **Специализация** — лабораторные протоколы и методики анализа
- 🔍 **RAG-поиск** — векторный поиск по базе знаний Supabase (`knowledge_base`)
- 🤖 **DeepSeek / OpenRouter** — современные LLM через API
- 💬 **Эмбеддинги** — `intfloat/multilingual-e5-large` через Hugging Face API (1024 dim)
- 💾 **Кэширование** — SQLite кэш для эмбеддингов, ускоряет повторные запросы
- 🖼️ **Мультимодальность** — поддержка изображений в чате
- 🐳 **Docker** — полный стек в контейнерах

## Структура проекта

```
├── client/               # Фронтенд React + Vite
├── server/               # Бэкенд Node.js (Express)
├── shared/               # Общие схемы данных (Drizzle ORM)
├── embedding_server.py   # Python-сервер эмбеддингов (порт 8000)
├── embedding.py          # Логика генерации эмбеддингов (HF API)
├── rag_pipeline.py       # RAG-пайплайн (поиск + контекст)
├── rebuild_knowledge_base.py  # Индексация документов в Supabase
├── structured_uploader.py     # Загрузчик структурированных данных
├── docker-compose.yml    # Docker Compose конфиг
├── Dockerfile            # Node.js контейнер
├── Dockerfile.python     # Python контейнер
└── .env.example          # Пример переменных окружения
```

---

## 🚀 Развёртывание на сервере

### 1. Клонирование репозитория

```bash
git clone https://github.com/kirik99/boi3.git
cd boi3
```

### 2. Настройка переменных окружения

```bash
cp .env.example .env
nano .env
```

Заполни `.env`:

```env
OPENROUTER_API_KEY=sk-or-...       # ключ OpenRouter (openrouter.ai/keys)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...                # anon key из Supabase
HF_TOKEN=hf_...                    # токен Hugging Face (hf.co/settings/tokens)
DEEPSEEK_API_KEY=sk-...            # ключ DeepSeek (опционально)
```

### 3. Запуск через Docker (рекомендуется)

```bash
# Поднять все контейнеры
docker compose up -d --build

# Проверить логи
docker compose logs -f
```

Приложение доступно: **http://your-server-ip:5000**  
Сервер эмбеддингов: **http://your-server-ip:8000**

### 4. Запуск без Docker (локально)

```bash
# Установить зависимости Node.js
npm install

# Установить зависимости Python
pip install -r requirements.txt

# Запустить сервер эмбеддингов (терминал 1)
python embedding_server.py

# Запустить основное приложение (терминал 2)
npm run dev
```

Приложение: **http://localhost:5000**

---

## 📚 Наполнение базы знаний

После запуска — проиндексируй документы:

```bash
# Внутри контейнера
docker compose exec embedding python rebuild_knowledge_base.py

# Или локально
python embedding_server.py          # терминал 1
python rebuild_knowledge_base.py    # терминал 2
```

### Supabase — настройка функции поиска

В **Supabase SQL Editor** создай функцию для векторного поиска (1024 dim):

```sql
CREATE OR REPLACE FUNCTION match_chunks(
  query_embedding vector(1024),
  match_threshold float DEFAULT 0.5,
  match_count int DEFAULT 5
)
RETURNS TABLE (
  id bigint,
  content text,
  metadata jsonb,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT id, content, metadata,
    1 - (embedding <=> query_embedding) AS similarity
  FROM knowledge_base
  WHERE 1 - (embedding <=> query_embedding) > match_threshold
  ORDER BY embedding <=> query_embedding
  LIMIT match_count;
$$;
```

---

## 🔄 Обновление приложения на сервере

```bash
git pull
docker compose up -d --build
```

---

## Лицензия

MIT