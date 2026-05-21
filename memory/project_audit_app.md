---
name: project-audit-app
description: Ponderosa prototype audit app architecture — services, pipeline, and design decisions
metadata:
  type: project
---

Ponderosa is building a prototype AI property audit system alongside the marketing site. Users walk their property with their phone, the client filters and uploads sharp frames, and a backend pipeline generates a personalized fire-risk report via Claude.

**Pipeline:**
1. Client (`app.html` at app.ponderosafireprotection.com) — vanilla JS, no framework
2. Intake service (`services/intake`) — Python, RESTful, at api.ponderosafireprotection.com
3. Recommender (`services/recommender`) — Python daemon, uses Claude to analyze image+pose pairs, outputs MD report
4. Presenter (`services/presenter`) — Python daemon, renders MD into static HTML survey page at surveys.ponderosafireprotection.com/<id>

**Inter-service comms:** named pipes (FIFOs); work queue is FS directories named by geohash survey ID.

**Why:** Prototype-grade simplicity — no message broker, no containerization overhead. Named pipes and FS directories are intentional for now.

**How to apply:** Don't suggest over-engineered IPC (Redis, RabbitMQ, etc.) unless the user asks to scale beyond prototype. Keep suggestions aligned with the FS-based queue model.
