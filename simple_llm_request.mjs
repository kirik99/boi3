/**
 * Простой скрипт для отправки запросов в LLM через OpenRouter API
 */
import fetch from 'node-fetch';

const API_KEY = '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';
const API_URL = 'https://openrouter.ai/api/v1/chat/completions';

async function sendRequest(userMessage, imageUrl = null) {
  console.log('Отправляем запрос в LLM...');
  
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
            { type: "text", text: userMessage },
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
          content: userMessage
        }
      ];
    }

    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'openai/gpt-4o', // или другая подходящая модель
        messages: messages,
        temperature: 0.7,
      })
    });

    if (!response.ok) {
      const errorData = await response.text();
      throw new Error(`Ошибка API: ${response.status} - ${errorData}`);
    }

    const data = await response.json();
    console.log('\nОтвет от LLM:');
    console.log(data.choices[0].message.content);
    
    return data.choices[0].message.content;
  } catch (error) {
    console.error('Ошибка при отправке запроса:', error.message);
  }
}

// Примеры использования
console.log('=== Демонстрация работы с API ===\n');

// Пример текстового запроса
console.log('1. Текстовый запрос:');
await sendRequest('Объясни, как работает искусственный интеллект.');

setTimeout(async () => {
  console.log('\n2. Мультимодальный запрос (если есть изображение):');
  // Пример с изображением (замените на реальный URL изображения)
  // await sendRequest('Что ты видишь на этом изображении?', 'https://example.com/image.jpg');
}, 2000);

setTimeout(async () => {
  console.log('\n3. Еще один текстовый запрос:');
  await sendRequest('Какие преимущества у использования нейросетей в разработке?');
}, 4000);