.PHONY: serve install clean

/tmp/ponderosa.http.pid:
	python serve.py & echo $$! > $@

serve: /tmp/ponderosa.http.pid
	echo "HTTP server running"
	

REPO_DIR := $(shell pwd)
SITE_AVAILABLE := /etc/nginx/sites-available/ponderosafireprotection.com
SITE_ENABLED   := /etc/nginx/sites-enabled/ponderosafireprotection.com

SECRETS_FILE := /etc/ponderosa/secrets.env

install: provision-secrets install-site install-intake install-recommender install-presenter

provision-secrets:
	@mkdir -p /etc/ponderosa
	@chmod 700 /etc/ponderosa
	@if [ ! -f $(SECRETS_FILE) ]; then \
		touch $(SECRETS_FILE); \
		chmod 600 $(SECRETS_FILE); \
	fi
	@if ! grep -q '^ANTHROPIC_API_KEY=' $(SECRETS_FILE) 2>/dev/null; then \
		printf 'ANTHROPIC_API_KEY: '; \
		read -r key; \
		echo "ANTHROPIC_API_KEY=$$key" >> $(SECRETS_FILE); \
		echo "  Written to $(SECRETS_FILE)"; \
	else \
		echo "  ANTHROPIC_API_KEY already set in $(SECRETS_FILE)"; \
	fi

install-site:
	rsync -a --delete root/var/www/ponderosafireprotection.com/ /var/www/ponderosafireprotection.com/
	cp root/etc/nginx/sites-available/ponderosafireprotection.com $(SITE_AVAILABLE)
	ln -sf $(SITE_AVAILABLE) $(SITE_ENABLED)
	nginx -t && systemctl reload nginx

install-intake:
	$(MAKE) -C ../services/intake install

install-recommender:
	$(MAKE) -C ../services/recommender install

install-presenter:
	$(MAKE) -C ../services/presenter install

clean:
	kill $$(cat /tmp/ponderosa.http.pid) && rm /tmp/ponderosa.http.pid