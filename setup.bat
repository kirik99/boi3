#!/bin/bash
# Скрипт для запуска мультимодального AI-агента

echo "🚀 Запуск мультимодального AI-агента..."

# Проверяем наличие необходимых зависимостей
if ! command -v node &> /dev/null; then
    echo "❌ Node.js не установлен. Пожалуйста, установите Node.js."
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm не установлен. Пожалуйста, установите Node.js и npm."
    exit 1
fi

echo "✅ Node.js и npm установлены"

# Устанавливаем зависимости
echo "📦 Устанавливаем зависимости..."
npm install
npm install --save-dev cross-env
npm install better-sqlite3
npm install --save-dev @types/better-sqlite3

# Проверяем наличие .env файла
if not exist .env (
    echo ⚠️  Файл .env не найден. Создаем шаблон...
    echo OPENROUTER_API_KEY=your_api_key_here > .env
    echo    ⚠️  Please replace 'your_api_key_here' with your actual API key in .env file
)

echo "✅ Зависимости установлены"

echo "💡 Для запуска приложения выполните:"
echo "   npm run dev"
echo ""
echo "🌐 Приложение будет доступно по адресу: http://localhost:5000"