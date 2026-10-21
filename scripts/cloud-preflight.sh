#!/bin/sh
# Read-only inventory. Never print environment, secrets or container arguments.
set -eu
printf '\nYOUAI server preflight\n'
printf '\nOS\n'
if [ -r /etc/os-release ]; then sed -n '/^PRETTY_NAME=/p' /etc/os-release; fi
uname -m
printf '\nCPU and memory\n'
getconf _NPROCESSORS_ONLN
free -m
printf '\nDisk capacity\n'
df -h / /var /tmp
printf '\nListening TCP ports\n'
if command -v ss >/dev/null 2>&1; then ss -ltn; else printf 'ss unavailable\n'; fi
printf '\nDocker availability\n'
if command -v docker >/dev/null 2>&1; then
  docker --version
  if docker info --format '{{.ServerVersion}}' 2>/dev/null; then
    docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
    docker compose version || true
  else
    printf 'Docker daemon unavailable or current account lacks access\n'
  fi
else
  printf 'Docker is not installed\n'
fi
printf '\nDeployment prerequisites\n'
for tool in curl openssl tar; do
  if command -v "$tool" >/dev/null 2>&1; then printf '%s: available\n' "$tool"; else printf '%s: missing\n' "$tool"; fi
done
printf '\nInventory complete. Domain, ICP, firewall and backups require separate verification.\n'
