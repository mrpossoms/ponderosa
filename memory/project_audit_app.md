---
name: project-audit-app
description: Ponderosa prototype audit app architecture — services, pipeline, and design decisions
metadata:
  type: project
---

Ponderosa is building a prototype AI property audit system alongside the marketing site. Users walk their property with their phone, the client filters and uploads sharp frames, and a backend pipeline generates a personalized fire-risk report via Claude.

**Pipeline:**
1. Client (`app.html` at app.ponderosafireprotection.com) — vanilla JS, no framework. Wizard: intro → email → perms → record → upload → done.
2. Email collected before permissions; sent with trajectory POST. Intake writes both `trajectory.json` (contains email) and `email.txt` per survey.
3. Intake service (`services/intake`) — FastAPI/uvicorn, at api.ponderosafireprotection.com. Deployed to `/opt/ponderosa/intake/` with venv at `.venv/` using `/usr/bin/python3`. Survey data in `/var/ponderosa/surveys/` owned by `www-data`.
4. Recommender (`services/recommender`) — Python daemon, uses Claude to analyze image+pose pairs, outputs MD report
5. Presenter (`services/presenter`) — Python daemon, renders MD into static HTML survey page at surveys.ponderosafireprotection.com/<id>

**Production server:** root@protean.io. Deploy with `make install` from `site/`. All subdomains on HTTPS via Let's Encrypt.

**Inter-service comms:** named pipes (FIFOs); work queue is FS directories named by geohash survey ID.

**Why:** Prototype-grade simplicity — no message broker, no containerization overhead. Named pipes and FS directories are intentional for now.

**How to apply:** Don't suggest over-engineered IPC (Redis, RabbitMQ, etc.) unless the user asks to scale beyond prototype. Keep suggestions aligned with the FS-based queue model.
