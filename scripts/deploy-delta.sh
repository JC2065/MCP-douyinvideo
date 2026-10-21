#!/usr/bin/env bash
# Code-only release from a Linux/macOS shell (same flow as deploy-platform.ps1 in delta mode).
# Usage: scripts/deploy-delta.sh [--key PATH] [--server root@HOST] [--dry-run]
# Env: DEPLOY_KEY, DEPLOY_SERVER, DEPLOY_KNOWN_HOSTS (e.g. the claude-deploy folder's known_hosts)
set -euo pipefail
cd "$(dirname "$0")/.."
KEY=${DEPLOY_KEY:-$HOME/.ssh/youai_deploy}; SERVER=${DEPLOY_SERVER:-root@182.61.14.185}; DRY=0
while [ $# -gt 0 ]; do case $1 in --key) KEY=$2; shift;; --server) SERVER=$2; shift;; --dry-run) DRY=1;; esac; shift; done
OPTS=(-i "$KEY" -o BatchMode=yes -o StrictHostKeyChecking=yes)
[ -z "${DEPLOY_KNOWN_HOSTS:-}" ] || OPTS+=(-o "UserKnownHostsFile=$DEPLOY_KNOWN_HOSTS")
SSH=(ssh "${OPTS[@]}" "$SERVER")
SCP=(scp "${OPTS[@]}")
[ -z "$(git status --porcelain -- scripts utils/platform-boundaries.json)" ] || { echo "commit scripts/ first" >&2; exit 1; }
TAG=platform-$(git rev-parse --short HEAD)
"${SCP[@]}" scripts/remote-release.sh "$SERVER:/opt/youai/releases/remote-release.sh"
LIVE=$("${SSH[@]}" bash /opt/youai/releases/remote-release.sh live)
echo "live: $LIVE   new: $TAG"
[ "$LIVE" != "$TAG" ] || { echo "already live"; exit 0; }
BASE=${LIVE#platform-}
if [[ ! $LIVE =~ ^platform-[0-9a-f]+$ ]] || ! git cat-file -e "$BASE^{commit}" 2>/dev/null \
   || git diff "$BASE" HEAD -- scripts/Dockerfile.video | grep -qE '^(-(FROM|RUN)|\+FROM)'; then
  echo "dependencies changed or live image unknown: run the full deploy (deploy-platform.cmd -Full)" >&2; exit 3
fi
# Added RUN/ENV lines (new dependencies, environment) are layered on top of the live image.
EXTRA=$(git diff "$BASE" HEAD -- scripts/Dockerfile.video | sed -n -E 's/^\+((RUN|ENV) .*)$/\1/p')
git diff --stat "$BASE" HEAD -- scripts utils/platform-boundaries.json | tail -1
[ $DRY = 0 ] || { echo "dry run: nothing uploaded"; exit 0; }
ARCHIVE=$(mktemp -t app-XXXX.tgz)
git archive --format=tar.gz -o "$ARCHIVE" HEAD scripts utils/platform-boundaries.json
"${SSH[@]}" mkdir -p "/opt/youai/releases/$TAG"
"${SCP[@]}" "$ARCHIVE" "$SERVER:/opt/youai/releases/$TAG/app.tgz"; rm -f "$ARCHIVE"
if [ -n "$EXTRA" ]; then echo "adding dependency layer:"; echo "$EXTRA"; printf '%s\n' "$EXTRA" | "${SSH[@]}" "cat > /opt/youai/releases/$TAG/extra.dockerfile"; fi
"${SSH[@]}" bash /opt/youai/releases/remote-release.sh build-delta "$TAG"
"${SSH[@]}" bash /opt/youai/releases/remote-release.sh switch "$TAG"
