/**
 * Клиент для работы с бесплатной моделью arcee-ai/trinity-large-preview:free
 */

import fetch from 'node-fetch';

// Конфигурация для бесплатной модели
const FREE_MODEL_CONFIG = {
  apiKey: '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',
  apiUrl: 'https://openrouter.ai/api/v1/chat/completions',
  model: 'arcee-ai/trinity-large-preview:free'
};

async function sendToFreeModel(message, imageUrl = null, config = FREE_MODEL_CONFIG) {
  console.log('Отправляем запрос в бесплатную модель arcee-ai/trinity-large-preview:free...');
  
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
    
    console.log('\n✅ Ответ от бесплатной модели:');
    console.log(content);
    
    return content;
  } catch (error) {
    console.error('❌ Ошибка при отправке запроса:', error.message);
    return null;
  }
}

// Функция для тестирования доступности бесплатной модели
async function testFreeModel() {
  console.log(`\n🧪 Тестируем бесплатную модель: ${FREE_MODEL_CONFIG.model}`);
  
  try {
    const response = await fetch(FREE_MODEL_CONFIG.apiUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${FREE_MODEL_CONFIG.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: FREE_MODEL_CONFIG.model,
        messages: [{ role: "user", content: "Привет, проверка связи." }],
        temperature: 0.1,
        max_tokens: 10,
      })
    });

    if (response.ok) {
      console.log(`✅ Бесплатная модель ${FREE_MODEL_CONFIG.model} доступна и готова к работе`);
      return true;
    } else {
      const errorData = await response.text();
      console.log(`❌ Модель вернула ошибку: ${response.status} - ${errorData}`);
      return false;
    }
  } catch (error) {
    console.log(`❌ Не удалось подключиться к модели: ${error.message}`);
    return false;
  }
}

// Основная функция
async function main() {
  console.log('🚀 Клиент для бесплатной модели arcee-ai/trinity-large-preview:free');
  console.log('===============================================================');
  
  // Тестирование бесплатной модели
  const isAvailable = await testFreeModel();
  
  if (isAvailable) {
    console.log('\n💡 Примеры запросов к бесплатной модели:');
    
    // Пример текстового запроса
    console.log('\n📝 Текстовый запрос:');
    await sendToFreeModel('Объясни, как работает искусственный интеллект.');
  } else {
    console.log('\n❌ Бесплатная модель недоступна. Проверьте API-ключ и подключение к интернету.');
  }
}

// Запуск основной функции
main().catch(console.error);