# Multi-Modal Agent Deployment Script
# Запускать на сервере (ПК, где будет приложение)

Write-Host "=== Multi-Modal Agent Deployment ===" -ForegroundColor Cyan

# 1. Проверка Node.js
Write-Host "`n[1/5] Checking Node.js..." -ForegroundColor Yellow
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Node.js not installed. Install from https://nodejs.org/" -ForegroundColor Red
    exit 1
}
Write-Host "Node.js: $(node --version)" -ForegroundColor Green

# 2. Проверка Python (для embedding сервера)
Write-Host "`n[2/5] Checking Python..." -ForegroundColor Yellow
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "WARNING: Python not found. Embedding server won't work." -ForegroundColor Yellow
} else {
    Write-Host "Python: $(python --version)" -ForegroundColor Green
}

# 3. Установка зависимостей
Write-Host "`n[3/5] Installing dependencies..." -ForegroundColor Yellow
npm install --production

# 4. Проверка .env
Write-Host "`n[4/5] Checking .env file..." -ForegroundColor Yellow
if (-not (Test-Path .env)) {
    Write-Host "WARNING: .env file not found. Copy .env.example to .env and fill in values." -ForegroundColor Yellow
    Write-Host "Run: copy .env.example .env" -ForegroundColor Yellow
} else {
    Write-Host ".env file found" -ForegroundColor Green
}

# 5. Сборка
Write-Host "`n[5/5] Building application..." -ForegroundColor Yellow
npm run build

# 6. Получение IP адреса
Write-Host "`n=== Network Information ===" -ForegroundColor Cyan
$ip = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" } | Select-Object -First 1 -ExpandProperty IPAddress
Write-Host "Local IP: $ip" -ForegroundColor Green
Write-Host "Access URL: http://$ip`:5000" -ForegroundColor Green
Write-Host "`n=== Starting Server ===" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow

# 7. Запуск сервера
npm run start
