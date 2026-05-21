.PHONY: serve install clean

/tmp/ponderosa.http.pid:
	python serve.py & echo $$! > $@

serve: /tmp/ponderosa.http.pid
	echo "HTTP server running"
	

REPO_DIR := $(shell pwd)
SITE_AVAILABLE := /etc/nginx/sites-available/ponderosafireprotection.com
SITE_ENABLED   := /etc/nginx/sites-enabled/ponderosafireprotection.com

install: install-site install-intake

install-site:
	rsync -a --delete root/var/www/ponderosafireprotection.com/ /var/www/ponderosafireprotection.com/
	cp root/etc/nginx/sites-available/ponderosafireprotection.com $(SITE_AVAILABLE)
	ln -sf $(SITE_AVAILABLE) $(SITE_ENABLED)
	nginx -t && systemctl reload nginx

install-intake:
	$(MAKE) -C ../services/intake install

clean:
	kill $$(cat /tmp/ponderosa.http.pid) && rm /tmp/ponderosa.http.pid