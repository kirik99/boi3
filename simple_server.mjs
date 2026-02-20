/**
 * Простой HTTP сервер для запуска мультимодального агента
 * Использует альтернативный подход для избежания проблем с сокетами
 */

import express from 'express';
import { createServer } from 'http';
import { registerRoutes } from './server/routes.js';
import { log } from './server/index.js';

const app = express();
const httpServer = createServer(app);

// Middleware для обработки JSON
app.use(express.json());

// Регистрация маршрутов
await registerRoutes(httpServer, app);

// Обработка ошибок
app.use((err, req, res, next) => {
  const status = err.status || err.statusCode || 500;
  const message = err.message || "Internal Server Error";

  console.error("Internal Server Error:", err);

  if (res.headersSent) {
    return next(err);
  }

  return res.status(status).json({ message });
});

// Запуск сервера на порту 5000
const port = 5000;
app.listen(port, '127.0.0.1', () => {
  log(`Server running on http://127.0.0.1:${port}`);
  console.log(`🚀 Мультимодальный AI-агент запущен на http://127.0.0.1:${port}`);
  console.log(`💡 Откройте браузер и перейдите по адресу для использования приложения`);
});