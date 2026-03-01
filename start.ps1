# Запуск Multi-Modal Agent (Embedding + Приложение)

Write-Host "=== Multi-Modal Agent Startup ===" -ForegroundColor Cyan

# Терминал 1: Embedding сервер
Write-Host "`n[1/2] Starting embedding server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "python embedding_server.py" -WindowStyle Normal

Start-Sleep -Seconds 2

# Терминал 2: Основное приложение
Write-Host "`n[2/2] Starting application..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "npm run dev" -WindowStyle Normal

Write-Host "`n=== Both services started ===" -ForegroundColor Green
Write-Host "Open: http://localhost:5000" -ForegroundColor Cyan
