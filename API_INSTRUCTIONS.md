# Инструкция по использованию API ключа OpenRouter

## Настройка

1. Получите API ключ на [https://openrouter.ai](https://openrouter.ai)
2. Создайте файл `.env` в корне проекта
3. Добавьте ключ: `OPENROUTER_API_KEY=ваш_ключ`

## Возможные ошибки

### 402 - Insufficient credits
Ошибка означает, что на аккаунте недостаточно средств.

**Решения:**
- Пополните баланс в разделе [Settings > Credits](https://openrouter.ai/settings/credits)
- Используйте бесплатные модели (например, `arcee-ai/trinity-large-preview:free`)

### Альтернативные провайдеры

Можно использовать другие API, изменив конфигурацию в коде:
- OpenAI API
- Anthropic API  
- Google Gemini API

## Использование

```bash
node simple_llm_request.mjs
```

## Формат ответа

```
Answer:
<clear explanation of the result>

If image analysis was performed:
What was found on the image:
- ...

Agent actions:
- sent request to API
- received response
- formed final result
```

## Безопасность

⚠️ **Никогда не коммитьте `.env` файл с ключами!**

- Храните ключи в переменных окружения
- Используйте `.env.example` как шаблон без реальных значений
- Не передавайте ключи третьим лицам
