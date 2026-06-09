#!/usr/bin/env bash
set -euo pipefail

domain="${1:?usage: sudo scripts/configure_https.sh DOMAIN [UPSTREAM_PORT]}"
upstream_port="${2:-8080}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root" >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y nginx certbot python3-certbot-nginx

ufw allow 80/tcp >/dev/null || true
ufw allow 443/tcp >/dev/null || true

cat > "/etc/nginx/sites-available/${domain}" <<EOF
server {
    listen 80;
    server_name ${domain};

    client_max_body_size 100m;

    if (\$request_uri ~* "^/login\\?redirect-to=(%2F|/)app(%2F|/)setup-wizard/?$") {
        return 302 /login?redirect-to=%2Fapp%2F3pl-warehouse;
    }

    location = / {
        return 302 /login;
    }

    location = /app {
        return 302 /desk/3pl-warehouse;
    }

    location = /app/ {
        return 302 /desk/3pl-warehouse;
    }

    location = /desk {
        return 302 /desk/3pl-warehouse;
    }

    location = /app/setup-wizard {
        return 302 /app/3pl-warehouse;
    }

    location = /app/setup-wizard/ {
        return 302 /app/3pl-warehouse;
    }

    location = /app/home {
        return 302 /desk/3pl-warehouse;
    }

    location = /apps {
        return 302 /desk/3pl-warehouse;
    }

    location = /docs/erpnext-3pl-demo-use-cases-ru.pdf {
        alias /opt/erpnext-3pl-platform/docs/erpnext-3pl-demo-use-cases-ru.pdf;
        default_type application/pdf;
        add_header Content-Disposition "attachment; filename=erpnext-3pl-demo-use-cases-ru.pdf";
    }

    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_set_header X-Forwarded-Host \$host;
    proxy_set_header X-Forwarded-Port \$server_port;

    location ~ ^/(app|desk)(/|$) {
        if (\$http_cookie ~* "user_id=Guest") {
            return 302 /login;
        }

        if (\$http_cookie ~* "system_user=no") {
            return 302 /client/receiving-notice/list;
        }

        proxy_read_timeout 120;
        proxy_redirect off;
        proxy_pass http://127.0.0.1:${upstream_port};
    }

    location /socket.io {
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_pass http://127.0.0.1:${upstream_port};
    }

    location / {
        proxy_read_timeout 120;
        proxy_redirect off;
        proxy_pass http://127.0.0.1:${upstream_port};
    }
}
EOF

ln -sf "/etc/nginx/sites-available/${domain}" "/etc/nginx/sites-enabled/${domain}"
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl enable --now nginx
systemctl reload nginx

certbot --nginx \
  -d "$domain" \
  --non-interactive \
  --agree-tos \
  --register-unsafely-without-email \
  --redirect

nginx -t
systemctl reload nginx

echo "HTTPS enabled for https://${domain}"
