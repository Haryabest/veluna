# Veluna — развёртывание на другом ПК

## Требования

- Docker Desktop (Windows / macOS) или Docker Engine (Linux)
- Git
- Для Telegram Mini App: HTTPS URL (домен или туннель Pinggy/ngrok)

## Быстрый старт (Docker, всё в контейнерах)

```bash
git clone <repo-url> veluna
cd veluna
cp .env.example .env
```

Заполните в `.env` минимум:

- `SECRET_KEY`, `JWT_SECRET_KEY` — длинные случайные строки
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_WEBAPP_URL` — публичный HTTPS URL Mini App (например `https://your-domain.com`)
- `GEN_API_KEY` — используется и для чата, и для генерации фото через Z-Image (gen-api.ru). `CIVITAI_API_KEY` — опционально, нужен только если `IMAGE_PROVIDER=civitai`
- `CORS_ORIGINS` — URL фронта, например `http://localhost,https://your-domain.com`

Запуск:

```bash
docker compose -f docker-compose.deploy.yml up -d --build
```

Откройте **http://localhost** — nginx отдаёт фронт, `/api/` проксируется на backend.

Проверка:

```bash
docker compose -f docker-compose.deploy.yml ps
curl http://localhost/health
```

Остановка:

```bash
docker compose -f docker-compose.deploy.yml down
```

С данными БД (volumes сохраняются):

```bash
docker compose -f docker-compose.deploy.yml down
# docker compose -f docker-compose.deploy.yml down -v   # удалить volumes
```

## Telegram-бот (Windows)

Бот часто **не работает внутри Docker** (VPN, блокировка `api.telegram.org`). На Windows запускайте на хосте:

```powershell
.\scripts\run-bot-local.ps1
```

В `.env` укажите `DATABASE_URL` с `127.0.0.1:5433` если Postgres в Docker с пробросом порта, либо оставьте как в `setup-env.ps1`.

## Локальная разработка (текущий ПК)

```powershell
.\scripts\veluna-up.ps1
```

Фронт на хосте: `http://127.0.0.1:3000`, бэкенд в Docker на `:8020`.

Пересборка только фронта:

```powershell
.\scripts\restart-frontend.ps1 -Rebuild
```

## Порты

| Сервис   | Deploy (nginx) | Dev (docker-compose.yml) |
|----------|----------------|---------------------------|
| Web      | 80             | 3000 (host) / 80 (nginx)  |
| Backend  | /api/          | 8020                      |
| Postgres | internal       | 5433                      |
| Redis    | internal       | 6379                      |
| MinIO    | /media/ (via frontend) | 9000              |

## Переменная порта HTTP

В `.env` можно задать `VELUNA_HTTP_PORT=8080` если порт 80 занят.

## Миграции

Выполняются автоматически при старте `backend` (`docker-entrypoint.sh` → `alembic upgrade head`).
