# Multi-Modal Agent + ngrok Launcher
# Запускает сервер и открывает публичный доступ

Write-Host "=== Multi-Modal Agent + ngrok ===" -ForegroundColor Cyan

# Проверка ngrok
if (-not (Get-Command ngrok -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: ngrok not installed." -ForegroundColor Red
    Write-Host "Install: winget install ngrok" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n[1/3] Starting server..." -ForegroundColor Yellow
$serverProcess = Start-Process powershell -ArgumentList "npm run start" -PassThru -WindowStyle Normal

Start-Sleep -Seconds 3

Write-Host "`n[2/3] Starting ngrok..." -ForegroundColor Yellow
$ngrokProcess = Start-Process ngrok -ArgumentList "http 5000" -PassThru -WindowStyle Normal

Write-Host "`n[3/3] Waiting for ngrok to generate URL..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "`n=== PUBLIC ACCESS READY ===" -ForegroundColor Green
Write-Host "Open ngrok dashboard to get your URL:" -ForegroundColor Cyan
Write-Host "http://127.0.0.1:4040" -ForegroundColor Green
Write-Host "`nSend the https://xxxx.ngrok.io link to users" -ForegroundColor Cyan
Write-Host "`nPress Ctrl+C to stop all services" -ForegroundColor Yellow

# Ожидание остановки
Wait-Process -Id $serverProcess.Id, $ngrokProcess.Id
