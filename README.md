# Интеллектуальный Лабораторный Ассистент (MML Agent)

Исследовательский проект аспирантуры по разработке мультимодального ИИ-ассистента для оптимизации работы с 
лабораторными протоколами, методиками анализа и документацией на базе архитектуры **Advanced RAG** (Retrieval-Augmented Generation).

---

## 🔬 Научная новизна и архитектура решения

Проект решает фундаментальную проблему "зашумления" контекста большими текстовыми массивами при поиске узкоспециализированных лабораторных инструкций. Для этого реализован многоступенчатый пайплайн извлечения данных:

### 1. Архитектура Advanced RAG
- **Query Expansion (Расширение запроса):** Исходный запрос пользователя на лету обрабатывается через LLM (DeepSeek) для генерации 3-5 научных синонимов и химических аббревиатур (например, *ABTS -> 2,2'-azino-bis(3-ethylbenzothiazoline-6-sulfonic acid)*). Это многократно повышает точность векторного матчинга.
- **Многоязычные эмбеддинги:** Использование полносвязной модели `intfloat/multilingual-e5-large` (Hugging Face) для перевода текста в 1024-мерные векторы, захватывающие семантику как на русском, так и на английском языках.
- **Гибридный поиск (Hybrid Retrieval):** Интеграция косинусного сходства (Vector Search via `pgvector`) с лексическим фоллбэком (Keyword Тext Search) в базе данных PostgreSQL.

### 2. Эвристическое реранжирование (Diversity & Heuristic Reranking)
Классический RAG страдает от доминирования длинных документов (например, теоретических учебников) над короткими (рабочие инструкции). В проекте реализован кастомный алгоритм реранжирования:
1. **Diversity Filter:** БД возвращает расширенную выборку (до 50 чанков), но пайплайн отбирает не более 2 фрагментов из одного файла.
2. **Scoring Function:** Окончательная релевантность пересчитывается с учетом математических штрафов за превышение объема текста и огромных бонусов за наличие кириллицы. Это гарантирует приоритет локальных русскоязычных методик.

---

## 🧩 Технологический стек

* **Frontend:** React 18, Vite, TailwindCSS, ReactMarkdown (стриминг ответов), Lucide Icons.
* **Backend (API & Chat):** Node.js, Express, Drizzle ORM (управление сессиями).
* **Backend (AI & ML):** Python 3.10, Flask, HuggingFace Hub.
* **Database & Vector Store:** Supabase (PostgreSQL + `pgvector`).
* **LLM Engine:** DeepSeek (`deepseek-chat`) / OpenRouter.

---

## 🗄️ Структура Базы Данных (Supabase)

Основой системы является унифицированная таблица `knowledge_base` и RPC-функция для расчета косинусного расстояния.

### Таблица `knowledge_base`
- `id` (bigint, PK) — Уникальный идентификатор.
- `file_source` (text) — Исходный файл (например, `3.docx`, `Food_Analysis.pdf`).
- `category` & `step_type` (text) — Метаданные категоризации метода.
- `content` (text) — Извлеченный текстовый фрагмент (chunk).
- `embedding` (vector(1024)) — Векторное представление текста.
- `metadata` (jsonb) — Дополнительные JSON-параметры.

### RPC-Функция матчинга
Вычисление метрики `1 - (embedding <=> query_embedding)`:
```sql
CREATE OR REPLACE FUNCTION match_chunks(
  query_embedding vector(1024),
  match_threshold float DEFAULT 0.12,
  match_count int DEFAULT 30
)
RETURNS TABLE (id bigint, content text, file_source text, similarity float)
LANGUAGE sql STABLE AS $$
  SELECT id, content, file_source, 1 - (embedding <=> query_embedding) AS similarity
  FROM knowledge_base
  WHERE 1 - (embedding <=> query_embedding) > match_threshold
  ORDER BY embedding <=> query_embedding LIMIT match_count;
$$;
```

---

## 📁 Топология проекта

```text
├── client/                     # Фронтенд (UI чата, сессии, рендеринг Markdown)
├── server/                     # Главный Node.js сервер (API, логика диалогов)
├── ai/                         # RAG-пайплайн и ML микросервис
│   ├── embedding_server.py     # Flask-сервер (порт 8000) для оркестрации
│   ├── embedding.py            # Интеграция с HuggingFace E5-Large
│   ├── rag_pipeline.py         # Ядро системы (Query Expansion, Retrieval, Reranking)
│   ├── universal_uploader.py   # Конвейер парсинга PDF/DOCX и ингестии в Supabase
│   └── structured_uploader.py  # LLM-assisted парсинг сложных структурированных методик
├── shared/                     # Drizzle ORM схемы
├── Dockerfile                  # Изоляция Node.js окружения
├── Dockerfile.python           # Изоляция ML окружения
└── docker-compose.yml          # Оркестрация мультиконтейнерного деплоя
```

---

## 🚀 Деплой и развертывание

### Подготовка окружения
Создайте файл `.env` в корне проекта (см. `.env.example`):
```env
SUPABASE_URL=https://[YOUR_INSTANCE].supabase.co
SUPABASE_KEY=[YOUR_SERVICE_KEY]
HF_TOKEN=[YOUR_HUGGINGFACE_TOKEN]
DEEPSEEK_API_KEY=[YOUR_DEEPSEEK_KEY]
```

### Запуск через Docker
```bash
# Инициализация кэш-баз
touch sqlite.db rag_cache.db

# Запуск изолированного кластера
docker compose up -d --build
```

### Локальный запуск (Development Mode)
```bash
# Терминал 1 (Python ML Microservice)
cd ai
python embedding_server.py

# Терминал 2 (Node.js API & React Webpack)
npm install
npm run dev
```

---

*Документация подготовлена для демонстрации и защиты исследовательского ИИ-проекта.*