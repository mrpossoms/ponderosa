# ── HTTP → HTTPS redirect ────────────────────────────────────────────────────
server {
    listen 80;
    server_name api.ponderosafireprotection.com;
    return 301 https://$host$request_uri;
}

# ── Intake API ────────────────────────────────────────────────────────────────
server {
    listen 443 ssl;
    server_name api.ponderosafireprotection.com;

    ssl_certificate     /etc/letsencrypt/live/ponderosafireprotection.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ponderosafireprotection.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    client_max_body_size 20M;

    location / {
        proxy_pass         http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_read_timeout 30s;
    }

    access_log /var/log/nginx/ponderosa-intake-access.log;
    error_log  /var/log/nginx/ponderosa-intake-error.log;
}
