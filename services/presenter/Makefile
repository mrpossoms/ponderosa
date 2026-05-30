.PHONY: install output

REPO_ROOT       := $(shell git -C "$(dir $(abspath $(lastword $(MAKEFILE_LIST))))" rev-parse --show-toplevel)
TEST_SURVEY     := $(REPO_ROOT)/test/survey
TEST_FRAMES     := $(REPO_ROOT)/test/data
OUTPUT_DIR      := /tmp/ponderosa/surveys
SURVEY_ID       := test-survey
AFFILIATES_FILE := $(REPO_ROOT)/services/presenter/root/var/ponderosa/affiliates.json

PYTHON := $(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)

PRESENTER_DIR   := /opt/ponderosa/presenter
SURVEYS_WEB     := /var/www/ponderosafireprotection.com/surveys
SITE_AVAILABLE  := /etc/nginx/sites-available/surveys.ponderosafireprotection.com
SITE_ENABLED    := /etc/nginx/sites-enabled/surveys.ponderosafireprotection.com
SYSTEMD_UNIT    := /etc/systemd/system/ponderosa-presenter.service

output:
	mkdir -p $(OUTPUT_DIR)/processed/$(SURVEY_ID)/frames $(OUTPUT_DIR)/web
	cp $(TEST_SURVEY)/assessment.json $(OUTPUT_DIR)/processed/$(SURVEY_ID)/assessment.json
	cp $(TEST_SURVEY)/trajectory.json $(OUTPUT_DIR)/processed/$(SURVEY_ID)/trajectory.json
	cp $(TEST_FRAMES)/*.jpg           $(OUTPUT_DIR)/processed/$(SURVEY_ID)/frames/
	PROCESSED_DIR=$(OUTPUT_DIR)/processed \
	SURVEYS_WEB=$(OUTPUT_DIR)/web \
	AFFILIATES_FILE=$(AFFILIATES_FILE) \
	$(PYTHON) -c "from main import present_survey; present_survey('$(SURVEY_ID)')"
	@echo "Report written to $(OUTPUT_DIR)/web/$(SURVEY_ID)/index.html"

install:
	mkdir -p $(PRESENTER_DIR)
	rsync -a --delete . $(PRESENTER_DIR)/
	/usr/bin/python3 -m venv $(PRESENTER_DIR)/.venv
	$(PRESENTER_DIR)/.venv/bin/pip install -q -e $(PRESENTER_DIR)
	mkdir -p $(SURVEYS_WEB)
	chown -R www-data:www-data $(SURVEYS_WEB)
	mkdir -p /var/ponderosa
	cp -n root/var/ponderosa/affiliates.json /var/ponderosa/affiliates.json || true
	cp root/etc/nginx/sites-available/surveys.ponderosafireprotection.com $(SITE_AVAILABLE)
	ln -sf $(SITE_AVAILABLE) $(SITE_ENABLED)
	cp root/etc/systemd/system/ponderosa-presenter.service $(SYSTEMD_UNIT)
	systemctl daemon-reload
	systemctl enable ponderosa-presenter
	systemctl restart ponderosa-presenter
	nginx -t && systemctl reload nginx
