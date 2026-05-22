.PHONY: install

PRESENTER_DIR   := /opt/ponderosa/presenter
SURVEYS_WEB     := /var/www/ponderosafireprotection.com/surveys
SITE_AVAILABLE  := /etc/nginx/sites-available/surveys.ponderosafireprotection.com
SITE_ENABLED    := /etc/nginx/sites-enabled/surveys.ponderosafireprotection.com
SYSTEMD_UNIT    := /etc/systemd/system/ponderosa-presenter.service

install:
	mkdir -p $(PRESENTER_DIR)
	rsync -a --delete . $(PRESENTER_DIR)/
	/usr/bin/python3 -m venv $(PRESENTER_DIR)/.venv
	$(PRESENTER_DIR)/.venv/bin/pip install -q -e $(PRESENTER_DIR)
	mkdir -p $(SURVEYS_WEB)
	chown -R www-data:www-data $(SURVEYS_WEB)
	cp root/etc/nginx/sites-available/surveys.ponderosafireprotection.com $(SITE_AVAILABLE)
	ln -sf $(SITE_AVAILABLE) $(SITE_ENABLED)
	cp root/etc/systemd/system/ponderosa-presenter.service $(SYSTEMD_UNIT)
	systemctl daemon-reload
	systemctl enable ponderosa-presenter
	systemctl restart ponderosa-presenter
	nginx -t && systemctl reload nginx
