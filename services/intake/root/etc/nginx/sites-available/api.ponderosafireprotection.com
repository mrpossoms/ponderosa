server {
    listen 80;
    server_name api.ponderosafireprotection.com;

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
