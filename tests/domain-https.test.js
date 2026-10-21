const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const config = fs.readFileSync(path.join(__dirname, '../deploy/youai888.nginx.conf'), 'utf8');

test('HTTPS gateway uses matching hosts, external certificate paths and modern TLS', () => {
  assert.match(config, /server_name youai888\.top www\.youai888\.top;/);
  assert.match(config, /return 301 https:\/\/youai888\.top\$request_uri;/);
  assert.match(config, /listen 443 ssl;/);
  assert.match(config, /ssl_protocols TLSv1\.2 TLSv1\.3;/);
  assert.match(config, /ssl_certificate \/opt\/youai\/tls-youai888\/fullchain\.pem;/);
  assert.match(config, /ssl_certificate_key \/opt\/youai\/tls-youai888\/privkey\.pem;/);
});

test('gateway preserves authenticated API prefix stripping without exposing database or internal data API', () => {
  assert.match(config, /location \^~ \/youai\//);
  assert.match(config, /proxy_pass http:\/\/127\.0\.0\.1:8765\/;/);
  assert.match(config, /proxy_set_header Authorization \$http_authorization;/);
  assert.match(config, /access_log off;/);
  assert.match(config, /location \/ \{ return 404; \}/);
  assert.doesNotMatch(config, /8080|5432|BEGIN .*PRIVATE KEY/);
});

test('upload endpoints get their own body limits without trailing-slash redirects', () => {
  const conf = fs.readFileSync(path.join(__dirname, '../deploy/youai888.nginx.conf'), 'utf8');
  assert.match(conf, /location = \/youai\/references\/upload \{\s*client_max_body_size 210m;/);
  assert.match(conf, /location = \/youai\/replica\/jobs \{\s*client_max_body_size 10m;/);
  assert.match(conf, /location \^~ \/youai\/board\/works \{\s*client_max_body_size 7m;/);
  assert.doesNotMatch(conf, /location \^~ \/youai\/board\/works\/ /);
});
