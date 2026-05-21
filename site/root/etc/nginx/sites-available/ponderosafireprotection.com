# ── HTTP → HTTPS redirect ────────────────────────────────────────────────────
server {
    listen 80;
    server_name ponderosafireprotection.com www.ponderosafireprotection.com app.ponderosafireprotection.com;
    return 301 https://$host$request_uri;
}

# ── Marketing site ────────────────────────────────────────────────────────────
server {
    listen 443 ssl;
    server_name ponderosafireprotection.com www.ponderosafireprotection.com;

    ssl_certificate     /etc/letsencrypt/live/ponderosafireprotection.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ponderosafireprotection.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    root /var/www/ponderosafireprotection.com/html;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    access_log /var/log/nginx/ponderosafireprotection-access.log;
    error_log  /var/log/nginx/ponderosafireprotection-error.log;
}

# ── Audit app ─────────────────────────────────────────────────────────────────
server {
    listen 443 ssl;
    server_name app.ponderosafireprotection.com;

    ssl_certificate     /etc/letsencrypt/live/ponderosafireprotection.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ponderosafireprotection.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    root /var/www/ponderosafireprotection.com/html;

    location / {
        try_files $uri /app.html;
    }

    access_log /var/log/nginx/ponderosa-app-access.log;
    error_log  /var/log/nginx/ponderosa-app-error.log;
}
