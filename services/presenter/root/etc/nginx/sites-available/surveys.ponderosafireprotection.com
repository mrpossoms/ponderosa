# ── HTTP → HTTPS redirect ────────────────────────────────────────────────────
server {
    listen 80;
    server_name surveys.ponderosafireprotection.com;
    return 301 https://$host$request_uri;
}

# ── Survey report pages ───────────────────────────────────────────────────────
server {
    listen 443 ssl;
    server_name surveys.ponderosafireprotection.com;

    ssl_certificate     /etc/letsencrypt/live/ponderosafireprotection.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ponderosafireprotection.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    root /var/www/ponderosafireprotection.com/surveys;

    location / {
        try_files $uri $uri/index.html =404;
    }

    access_log /var/log/nginx/ponderosa-surveys-access.log;
    error_log  /var/log/nginx/ponderosa-surveys-error.log;
}
