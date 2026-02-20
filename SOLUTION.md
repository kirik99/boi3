# Решение проблемы с API ключом OpenRouter

## Решение: Использование бесплатной модели

Проект настроен на использование бесплатной модели `arcee-ai/trinity-large-preview:free`.

## Проверка работоспособности

```bash
node free_model_client.mjs
```

## Запуск приложения

1. Установите зависимости:
```bash
npm install
```

2. Создайте `.env`:
```
OPENROUTER_API_KEY=ваш_api_ключ
```

3. Запустите:
```bash
npm run dev
```

4. Откройте: http://localhost:5000

## Формат ответа

```
Answer:
<clear explanation>

What was found on the image:
- ...

Agent actions:
- sent request to API
- received response
- formed final result
```

## Безопасность

⚠️ **Важно:**
- Не публикуйте API ключи в открытых репозиториях
- Используйте переменные окружения
- Регулярно меняйте ключи
