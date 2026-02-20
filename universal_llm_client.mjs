/**
 * Универсальный скрипт для отправки запросов в различные LLM API
 * Поддерживает OpenRouter, OpenAI и другие провайдеры
 */

import fetch from 'node-fetch';
import dotenv from 'dotenv';

dotenv.config();

// Конфигурация API - замените на свои ключи или используйте переменные окружения
const CONFIGS = {
  openrouter_free: {
    apiKey: process.env.OPENROUTER_API_KEY || 'your-api-key-here',
    apiUrl: 'https://openrouter.ai/api/v1/chat/completions',
    model: 'arcee-ai/trinity-large-preview:free'  // Бесплатная модель
  },
  openrouter: {
    apiKey: process.env.OPENROUTER_API_KEY || 'your-api-key-here',
    apiUrl: 'https://openrouter.ai/api/v1/chat/completions',
    model: 'openai/gpt-4o'
  },
  // Пример для OpenAI - раскомментируйте и настройте при наличии ключа
  /*
  openai: {
    apiKey: 'ваш-openai-api-ключ',
    apiUrl: 'https://api.openai.com/v1/chat/completions',
    model: 'gpt-4o'
  },
  */
  // Пример для Google Gemini - раскомментируйте и настройте при наличии ключа
  /*
  gemini: {
    apiKey: 'ваш-gemini-api-ключ',
    apiUrl: (key) => `https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=${key}`,
    model: 'gemini-pro'
  }
  */
};

async function sendToOpenRouter(message, imageUrl = null, config = CONFIGS.openrouter) {
  console.log('Отправляем запрос в OpenRouter...');
  
  try {
    // Подготовка сообщений
    let messages;
    if (imageUrl) {
      // Мультимодальный запрос (текст + изображение)
      messages = [
        {
          role: "system",
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
        },
        {
          role: "user",
          content: [
            { type: "text", text: message },
            { 
              type: "image_url", 
              image_url: { url: imageUrl }
            }
          ]
        }
      ];
    } else {
      // Текстовый запрос
      messages = [
        {
          role: "system",
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
        },
        {
          role: "user",
          content: message
        }
      ];
    }

    const response = await fetch(config.apiUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${config.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: config.model,
        messages: messages,
        temperature: 0.7,
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => response.text());
      const errorMessage = typeof errorData === 'string' ? errorData : errorData.error?.message || 'Unknown error';
      const errorCode = response.status;
      
      // Обработка специфичных ошибок
      if (errorCode === 402) {
        console.error(`Ошибка оплаты (402): ${errorMessage}`);
        console.log('Решение: Пополните баланс на https://openrouter.ai/settings/credits');
      } else if (errorCode === 401) {
        console.error(`Неверный API ключ (401): ${errorMessage}`);
        console.log('Решение: Проверьте правильность API ключа');
      } else if (errorCode === 429) {
        console.error(`Превышен лимит запросов (429): ${errorMessage}`);
        console.log('Решение: Подождите перед следующим запросом');
      } else {
        console.error(`Ошибка API (${errorCode}): ${errorMessage}`);
      }
      
      throw new Error(`Ошибка API: ${errorCode} - ${errorMessage}`);
    }

    const data = await response.json();
    const content = data.choices[0].message.content;
    
    console.log('\n✅ Ответ от LLM:');
    console.log(content);
    
    return content;
  } catch (error) {
    console.error('❌ Ошибка при отправке запроса:', error.message);
    return null;
  }
}

// Функция для тестирования доступности API
async function testApiKey(configName, config) {
  console.log(`\n🧪 Тестируем конфигурацию: ${configName}`);
  
  try {
    const response = await fetch(config.apiUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${config.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: config.model,
        messages: [{ role: "user", content: "Привет, проверка связи." }],
        temperature: 0.1,
        max_tokens: 10,
      })
    });

    if (response.ok) {
      console.log(`✅ API ${configName} доступен и готов к работе`);
      return true;
    } else {
      const errorData = await response.text();
      console.log(`❌ API ${configName} вернул ошибку: ${response.status} - ${errorData}`);
      return false;
    }
  } catch (error) {
    console.log(`❌ Не удалось подключиться к API ${configName}: ${error.message}`);
    return false;
  }
}

// Основная функция
async function main() {
  console.log('🚀 Универсальный LLM API клиент');
  console.log('================================');
  
  // Тестирование конфигураций
  for (const [name, config] of Object.entries(CONFIGS)) {
    await testApiKey(name, config);
  }
  
  console.log('\n💡 Примеры запросов:');
  
  // Пример текстового запроса
  console.log('\n📝 Текстовый запрос:');
  await sendToOpenRouter('Объясни, как работает искусственный интеллект.');
  
  // Пример запроса с изображением (когда будет доступно)
  /*
  console.log('\n🖼 Мультимодальный запрос:');
  await sendToOpenRouter('Что ты видишь на этом изображении?', 'URL_КАРТИНКИ');
  */
}

// Запуск основной функции
main().catch(console.error);