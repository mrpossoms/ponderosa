.PHONY: install

INTAKE_DIR      := /opt/ponderosa/intake
SITE_AVAILABLE  := /etc/nginx/sites-available/api.ponderosafireprotection.com
SITE_ENABLED    := /etc/nginx/sites-enabled/api.ponderosafireprotection.com
SYSTEMD_UNIT    := /etc/systemd/system/ponderosa-intake.service

install:
	mkdir -p $(INTAKE_DIR)
	rsync -a --delete . $(INTAKE_DIR)/
	/usr/bin/python3 -m venv $(INTAKE_DIR)/.venv
	$(INTAKE_DIR)/.venv/bin/pip install -q -e $(INTAKE_DIR)
	mkdir -p /var/ponderosa/surveys/pending /var/ponderosa/surveys/processed /var/ponderosa/pipes
	chown -R www-data:www-data /var/ponderosa
	cp root/etc/nginx/sites-available/api.ponderosafireprotection.com $(SITE_AVAILABLE)
	ln -sf $(SITE_AVAILABLE) $(SITE_ENABLED)
	cp root/etc/systemd/system/ponderosa-intake.service $(SYSTEMD_UNIT)
	systemctl daemon-reload
	systemctl enable ponderosa-intake
	systemctl restart ponderosa-intake
	nginx -t && systemctl reload nginx
