#!/usr/bin/env bash
# Private, restorable snapshot before a release. Never prints credentials.
set -euo pipefail
umask 077
DIR=/opt/youai/internal-api
ROOT=/opt/youai/backups
cd "$DIR"
TAG=$(sed -n 's/^VIDEO_TAG=//p' .env | tr -d '\r')
[[ "$TAG" =~ ^[a-zA-Z0-9._-]+$ ]] || { echo 'Invalid live tag'; exit 1; }
DEST="$ROOT/$(date -u +%Y%m%dT%H%M%SZ)-$TAG"
mkdir -p "$DEST"
chmod 700 "$ROOT" "$DEST"
docker image inspect "codexyouai-video:$TAG" > "$DEST/image.json"
docker compose -f compose.video-cloud.yml config > "$DEST/compose.resolved.yml"
printf '%s\n' "$TAG" > "$DEST/previous-tag"
resume() { docker compose -f compose.video-cloud.yml up -d --no-build --wait video; }
trap resume EXIT
docker compose -f compose.video-cloud.yml stop -t 60 video
# Stopping the writer keeps SQLite WAL files and media consistent together.
tar -czf "$DEST/internal-api.tgz" -C /opt/youai internal-api
docker exec youai-cloud-postgres-1 sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$DEST/backend.dump"
resume
trap - EXIT
docker save "codexyouai-video:$TAG" | gzip > "$DEST/image.tar.gz"
tar -czf "$DEST/nginx.tgz" -C /etc nginx
tar -tzf "$DEST/internal-api.tgz" > "$DEST/files.txt"
gzip -t "$DEST/image.tar.gz"
docker exec -i youai-cloud-postgres-1 pg_restore --list < "$DEST/backend.dump" > "$DEST/database-contents.txt"
(cd "$DEST"; sha256sum internal-api.tgz backend.dump image.tar.gz nginx.tgz > SHA256SUMS; sha256sum -c SHA256SUMS)
chmod 600 "$DEST"/*
printf 'BACKUP=%s\n' "$DEST"
du -sh "$DEST"
