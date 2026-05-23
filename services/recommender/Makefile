.PHONY: install

RECOMMENDER_DIR := /opt/ponderosa/recommender
SYSTEMD_UNIT    := /etc/systemd/system/ponderosa-recommender.service

install:
	mkdir -p $(RECOMMENDER_DIR)
	rsync -a --delete . $(RECOMMENDER_DIR)/
	/usr/bin/python3 -m venv $(RECOMMENDER_DIR)/.venv
	$(RECOMMENDER_DIR)/.venv/bin/pip install -q -e $(RECOMMENDER_DIR)
	cp root/etc/systemd/system/ponderosa-recommender.service $(SYSTEMD_UNIT)
	systemctl daemon-reload
	systemctl enable ponderosa-recommender
	systemctl restart ponderosa-recommender
