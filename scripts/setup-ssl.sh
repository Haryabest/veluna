#!/bin/bash
# Obtain Let's Encrypt certificate and start Veluna with HTTPS.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

DOMAIN="${VELUNA_DOMAIN:-}"
if [ -z "$DOMAIN" ]; then
  echo "Set VELUNA_DOMAIN in .env (e.g. cristinavilyavina.fvds.ru)"
  exit 1
fi

echo "==> Stopping nginx to free port 80..."
docker compose stop nginx 2>/dev/null || true

echo "==> Requesting certificate for ${DOMAIN}..."
if ! command -v certbot >/dev/null 2>&1; then
  apt-get update
  apt-get install -y certbot
fi

certbot certonly --standalone -d "$DOMAIN" --non-interactive --agree-tos -m "${SSL_EMAIL:-admin@${DOMAIN}}" || \
  certbot certonly --standalone -d "$DOMAIN"

echo "==> Opening firewall ports..."
if command -v ufw >/dev/null 2>&1; then
  ufw allow 80/tcp || true
  ufw allow 443/tcp || true
fi

echo "==> Starting stack with HTTPS..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

echo "==> Done. Test:"
echo "  curl -I https://${DOMAIN}"
