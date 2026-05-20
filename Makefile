.PHONY: serve install

serve:
	python -m http.server -d root/var/www/ponderosafireprotection.com/html

REPO_DIR := $(shell pwd)
SITE_AVAILABLE := /etc/nginx/sites-available/ponderosafireprotection.com
SITE_ENABLED   := /etc/nginx/sites-enabled/ponderosafireprotection.com

install:
	ln -sf $(REPO_DIR)/root/var/www/ponderosafireprotection.com /var/www/ponderosafireprotection.com
	ln -sf $(REPO_DIR)/root/etc/nginx/sites-available/ponderosafireprotection.com $(SITE_AVAILABLE)
	ln -sf $(SITE_AVAILABLE) $(SITE_ENABLED)
	nginx -t && systemctl reload nginx
