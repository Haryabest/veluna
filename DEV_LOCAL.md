# Локальная разработка Veluna (4 терминала)

## Текущие URL (Cloudflare Quick Tunnel)

| Сервис | URL |
|--------|-----|
| **Frontend (Mini App)** | см. `TELEGRAM_WEBAPP_URL` в `.env` |
| **Backend API** | см. `NEXT_PUBLIC_API_URL` в `frontend/.env.local` |

При блокировке Cloudflare (FlClashX): `npx localtunnel --port 3000` и `--port 8002`, затем `.\scripts\veluna-dev-up.ps1` или обновить `.env` вручную.

> URL меняются после перезапуска туннелей. Смотри логи: `docker logs veluna-cf-front` / `docker logs veluna-cf-back`

## 1. Инфра

```powershell
cd C:\Users\Dima\veluna
docker compose up postgres redis minio -d
```

## 2. Туннели Cloudflare (Docker, protocol http2)

```powershell
docker rm -f veluna-cf-front veluna-cf-back
docker run -d --name veluna-cf-front cloudflare/cloudflared:latest tunnel --protocol http2 --url http://host.docker.internal:3000
docker run -d --name veluna-cf-back cloudflare/cloudflared:latest tunnel --protocol http2 --url http://host.docker.internal:8000
docker logs veluna-cf-front 2>&1 | findstr trycloudflare
docker logs veluna-cf-back 2>&1 | findstr trycloudflare
```

Нативно (если `winget install Cloudflare.cloudflared`):

```powershell
cloudflared tunnel --url http://127.0.0.1:3000
cloudflared tunnel --url http://127.0.0.1:8000
```

## 3. Backend

```powershell
cd backend
.\.venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

`.env` в корне — `DATABASE_URL` на `127.0.0.1` (не `postgres`).

## 4. Frontend

```powershell
cd frontend
npm run dev
```

`frontend/.env.local` — API на backend-туннель.

## 5. Telegram-бот

```powershell
cd backend
python -m app.bot.main
```

## BotFather

Menu Button URL: см. `TELEGRAM_WEBAPP_URL` в `.env` (меняется после каждого перезапуска туннеля)

## Быстрый скрипт

```powershell
.\scripts\dev-local.ps1
```
