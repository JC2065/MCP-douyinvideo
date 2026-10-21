#!/usr/bin/env bash
# Runs ON THE SERVER. Uploaded by deploy-platform.ps1 / deploy-delta.sh to /opt/youai/releases/remote-release.sh.
#   remote-release.sh live              print the live VIDEO_TAG
#   remote-release.sh build-delta TAG   build codexyouai-video:TAG = live image + /opt/youai/releases/TAG/app.tgz
#   remote-release.sh switch TAG        back up, switch VIDEO_TAG, health-check, auto-rollback on failure
set -euo pipefail
DIR=/opt/youai/internal-api
REL=/opt/youai/releases
cd "$DIR"
live() { grep '^VIDEO_TAG=' .env | cut -d= -f2; }

case "${1:-}" in
  live)
    live ;;
  build-delta)
    TAG=$2; LIVE=$(live); WORK=$REL/$TAG/build
    rm -rf "$WORK"; mkdir -p "$WORK/app"
    tar -xzf "$REL/$TAG/app.tgz" -C "$WORK/app"
    { printf 'FROM codexyouai-video:%s\n' "$LIVE"; [ ! -f "$REL/$TAG/extra.dockerfile" ] || cat "$REL/$TAG/extra.dockerfile"; printf 'COPY app/ /app/\n'; } > "$WORK/Dockerfile"
    echo "building $TAG on top of $LIVE (code-only layer)"
    docker build -q -t "codexyouai-video:$TAG" "$WORK"
    [ ! -f "$REL/$TAG/extra.dockerfile" ] || echo "dependency layer added"
    docker run -i --rm --entrypoint python "codexyouai-video:$TAG" - < "$WORK/app/scripts/check-image-modules.py"
    rm -rf "$WORK" ;;
  switch)
    TAG=$2; mkdir -p "$REL/$TAG"
    cp .env "$REL/$TAG/env.previous"
    cp compose.video-cloud.yml "$REL/$TAG/compose.previous.yml"
    live > "$REL/$TAG/previous-tag"
    tar -czf "$REL/$TAG/admin-data.tgz" -C video-data admin
    chmod 600 "$REL/$TAG/env.previous" "$REL/$TAG/admin-data.tgz"
    echo "backed up: $(cat "$REL/$TAG/previous-tag")"
    sed -i "s/^VIDEO_TAG=.*/VIDEO_TAG=$TAG/" .env
    if docker compose -f compose.video-cloud.yml up -d --no-build --wait video \
       && curl -fsS --max-time 5 http://127.0.0.1:8765/health >/dev/null \
       && [ "$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:8765/admin-api/platform)" = 401 ]; then
      echo "deployed $TAG"
    else
      echo "health check failed, restoring previous release" >&2
      cp "$REL/$TAG/env.previous" .env
      docker compose -f compose.video-cloud.yml up -d --no-build --wait video
      exit 1
    fi ;;
  *) echo "usage: remote-release.sh live|build-delta TAG|switch TAG" >&2; exit 2 ;;
esac
