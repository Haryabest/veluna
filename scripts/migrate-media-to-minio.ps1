# Upload external images from PostgreSQL into MinIO and update URLs in DB.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
docker exec -w /app veluna-backend python -m scripts.migrate_media_to_minio
