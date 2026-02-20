# Запуск мультимодального AI-агента в Replit

## Шаги для запуска

1. Перейдите на [https://replit.com](https://replit.com)

2. Импортируйте проект:
   - Используйте "Import from GitHub"
   - Или загрузите файлы вручную

3. Установите зависимости:
```bash
npm install
npm install --save-dev cross-env
```

4. Создайте `.env` файл:
```
OPENROUTER_API_KEY=ваш_api_ключ
```

5. Запустите:
```bash
npm run dev
```

## Используемая модель

Проект использует `arcee-ai/trinity-large-preview:free` — бесплатная модель.

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

⚠️ Не коммитьте `.env` с реальными ключами в репозиторий!
