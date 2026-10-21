#!/bin/sh
# Run on the target host. Creates credentials once; never rotates existing data.
set -eu
deploy_root=${1:?Usage: bootstrap-cloud.sh /absolute/deployment/path image-tag}
release_tag=${2:?Missing release tag}
case "$deploy_root" in /*) ;; *) echo 'Deployment path must be absolute' >&2; exit 1;; esac
case "$release_tag" in *[!a-zA-Z0-9._-]*|'') echo 'Invalid release tag' >&2; exit 1;; esac
if [ -e "$deploy_root/.env" ] || [ -e "$deploy_root/tls" ]; then
  echo 'Existing credentials or TLS directory found; preserve and inspect before provisioning' >&2
  exit 1
fi
mkdir -p "$deploy_root/tls"
chmod 755 "$deploy_root/tls"
umask 077
openssl req -x509 -newkey rsa:3072 -nodes -days 3650 -keyout "$deploy_root/tls/ca.key" -out "$deploy_root/tls/ca.crt" -subj '/CN=YOUAI Database CA' 2>/dev/null
openssl req -newkey rsa:3072 -nodes -keyout "$deploy_root/tls/server.key" -out "$deploy_root/tls/server.csr" -subj '/CN=postgres' 2>/dev/null
printf 'subjectAltName=DNS:postgres\nbasicConstraints=CA:FALSE\nextendedKeyUsage=serverAuth\n' > "$deploy_root/tls/server.ext"
openssl x509 -req -in "$deploy_root/tls/server.csr" -CA "$deploy_root/tls/ca.crt" -CAkey "$deploy_root/tls/ca.key" -CAcreateserial -out "$deploy_root/tls/server.crt" -days 825 -extfile "$deploy_root/tls/server.ext" 2>/dev/null
# postgres:16-alpine runs PostgreSQL as UID 70.
chown 70:70 "$deploy_root/tls/server.key"
chmod 600 "$deploy_root/tls/server.key"
chmod 644 "$deploy_root/tls/server.crt" "$deploy_root/tls/ca.crt"
python3 - "$deploy_root" "$release_tag" <<'PY'
import pathlib, secrets, sys
root=pathlib.Path(sys.argv[1])
ca=(root/'tls/ca.crt').read_text().replace('\n',r'\n')
with (root/'.env').open('x') as stream:
    stream.write('DB_PASSWORD='+secrets.token_hex(32)+'\nAPI_TAG='+sys.argv[2]+'\nDATABASE_CA="'+ca+'"\n')
(root/'.env').chmod(0o600)
PY
openssl verify -CAfile "$deploy_root/tls/ca.crt" -verify_hostname postgres "$deploy_root/tls/server.crt"
echo 'Production credentials created; do not print .env or private keys.'
