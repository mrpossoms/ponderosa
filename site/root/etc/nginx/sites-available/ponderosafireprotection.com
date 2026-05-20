server {
    listen 80;
    server_name ponderosafireprotection.com www.ponderosafireprotection.com;

    root /var/www/ponderosafireprotection.com/html;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    access_log /var/log/nginx/ponderosafireprotection-access.log;
    error_log  /var/log/nginx/ponderosafireprotection-error.log;
}
