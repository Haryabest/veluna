#!/bin/sh
set -e

if [ -z "$VELUNA_DOMAIN" ]; then
  echo "VELUNA_DOMAIN is required for SSL nginx"
  exit 1
fi

if [ ! -f "/etc/letsencrypt/live/${VELUNA_DOMAIN}/fullchain.pem" ]; then
  echo "SSL certificate not found: /etc/letsencrypt/live/${VELUNA_DOMAIN}/fullchain.pem"
  echo "Run: sudo certbot certonly --standalone -d ${VELUNA_DOMAIN}"
  exit 1
fi

envsubst '${VELUNA_DOMAIN}' < /etc/nginx/nginx.ssl.conf.template > /etc/nginx/nginx.conf
exec nginx -g 'daemon off;'
