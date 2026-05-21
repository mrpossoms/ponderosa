.PHONY: dev stop install

dev: /tmp/ponderosa.http.pid /tmp/ponderosa.intake.pid
	@echo "All services running"

/tmp/ponderosa.http.pid:
	$(MAKE) -C site serve

/tmp/ponderosa.intake.pid:
	services/intake/run.sh --dev &

install:
	$(MAKE) -C site install
	$(MAKE) -C services/intake install

stop:
	@kill $$(cat /tmp/ponderosa.http.pid)   && rm /tmp/ponderosa.http.pid   || true
	@kill $$(cat /tmp/ponderosa.intake.pid) && rm /tmp/ponderosa.intake.pid || true
