# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

**Ponderosa Fire Protection** — a Colorado wildfire defense company. The repo contains two things:

1. **Marketing site** — static HTML/CSS in `site/`
2. **Property audit app** — a prototype AI-powered system that guides users through recording their property, analyzes footage with an LLM, and generates a personalized fire-risk report

## Commands

### Dev system — start all services

```sh
# Terminal 1 — app HTTP server
cd site/root/var/www/ponderosafireprotection.com/html && python3 -m http.server 8080

# Terminal 2 — test data server (real frames for Playwright mock camera)
cd /path/to/repo && python3 test/serve.py   # serves test/data/ on :8082

# Terminal 3 — intake API
cd services/intake && ./run.sh --dev

# Terminal 4 — recommender (requires API key)
cd services/recommender && ./run.sh --dev   # reads ANTHROPIC_API_KEY from .secrets.env

# Terminal 5 — presenter
cd services/presenter && ./run.sh --dev
```

### Marketing site — run from `site/`

```sh
make serve    # local dev server at http://localhost:8000 (Python http.server)
make install  # deploy everything to production (prompts for ANTHROPIC_API_KEY if missing)
```

## Structure

```
site/
  Makefile              # top-level install + provision-secrets target
  setup-mail.sh         # Postfix + OpenDKIM setup script for production
  root/
    etc/nginx/sites-available/ponderosafireprotection.com
    var/www/ponderosafireprotection.com/html/
      styles.css        # shared base styles
      index.html        # coming soon landing page
      home.html         # full marketing site
      app.html          # audit app client

services/
  README.md             # pipeline overview
  intake/               # FastAPI — session creation, frame + trajectory ingest
  recommender/          # daemon — Claude vision assessment of all frames in one call
  presenter/            # daemon — HTML report generation + email notification

test/
  serve.py              # CORS file server for test/data/ on :8082
  data/                 # real property photos for Playwright end-to-end testing
    1.jpg … 5.jpg
```

### Service subdomains

- `ponderosafireprotection.com` — marketing site
- `app.ponderosafireprotection.com` — audit client app
- `api.ponderosafireprotection.com` — intake service
- `surveys.ponderosafireprotection.com/<session_id>/` — generated survey report pages (trailing slash required for relative image paths)

### Audit app wizard screens (`app.html`)

1. **Request** (`#screen-request`) — email form; calls `POST /session`, transitions to check-email screen
2. **Check email** (`#screen-check`) — "check your email" confirmation
3. **Permissions** (`#screen-perms`) — requests camera, GPS, motion; shown directly when `?session=` is in URL
4. **Record** (`#screen-record`) — live viewfinder, HUD with frame count + GPS status, record/finish buttons
5. **Upload** (`#screen-upload`) — indeterminate animated bar while frames in-flight, per-frame counter as each settles
6. **Done** (`#screen-done`) — success confirmation

On load, `app.html` reads `?session=` from the URL. If present, jumps directly to permissions. If absent, shows the email request screen.

### Audit app pipeline

1. User submits email → intake creates a session token, emails a magic link to `app.ponderosafireprotection.com?session=<token>`
2. User opens magic link → app extracts session token from URL, uses it as the survey ID for all uploads
3. Client records video via `getUserMedia`, scores frames client-side (variance of Laplacian), POSTs only sharp frames as JPEG to intake (best-effort, tracked as promises)
4. On finish: waits for all frame POSTs, then POSTs trajectory JSON
5. Intake validates session token on every request (403 if invalid), stores frames + trajectory, signals recommender via named pipe
6. Recommender sends **all frames in a single Claude API call** (`claude-haiku-4-5-20251001`) with interleaved image+pose content blocks; parses JSON response: `{ rating, summary, frames: [{frame, urgency, assessment, actions[]}] }`
7. Recommender moves survey to `processed/`, signals presenter via named pipe
8. Presenter filters frames (urgency > mean, or novel action); reads frame dimensions with Pillow to choose portrait vs landscape card layout; renders HTML report + sends email with report link

### Inter-service communication

Named pipes (FIFOs) on the filesystem — intake → recommender → presenter. Each daemon reopens the pipe in a `while True` loop so it stays alive after each EOF (FIFOs close when the writer disconnects).

### Secrets management

- **Production:** `/etc/ponderosa/secrets.env` (chmod 600, root-owned). Referenced via `EnvironmentFile=` in `ponderosa-recommender.service`. `make install` prompts for `ANTHROPIC_API_KEY` if not already set.
- **Dev:** `services/recommender/.secrets.env` — sourced by `run.sh --dev`. Gitignored.

## Site architecture (marketing)

`index.html` is the coming soon page. `home.html` is the full marketing site with sections: Nav, Hero, Problem, System, Tiers, Process, Differentiator, Partners, Service area, Testimonials, FAQ, CTA/Form, Footer.

## CSS conventions

Shared base styles live in `styles.css`. Page-specific styles are in inline `<style>` blocks. CSS custom properties on `:root` define the color palette:

- `--orange` / `--orange-deep` / `--ember` — brand fire tones
- `--black` / `--char` / `--char-2` — dark backgrounds
- `--cream` / `--paper` — light text and cream section backgrounds
- `--line` / `--line-strong` — subtle border alphas

Typography: **Bebas Neue** (display), **Oswald** (labels/UI), **Inter** (body). Breakpoints are inline `@media` blocks adjacent to each component.

## UI automation (Playwright MCP)

A Playwright MCP server is configured in `.mcp.json` so Claude can drive the app directly.

**Setup:**
- MCP server: `npx @playwright/mcp` (config in `.mcp.json`)
- Browser: **WebKit** (Safari engine) with `--device "iPhone 15"` emulation
- Init script: `.claude/mock-camera.js` — injected into every page, mocks:
  - `getUserMedia` → fetches real test frames from `http://localhost:8082/data/` and cycles through them (one per 3s so the 2000ms cooldown passes between frames)
  - `DeviceMotionEvent.requestPermission` → auto-grants
  - `navigator.geolocation` → fixed Denver, CO coordinates

**To use:**
1. Start all dev services (see above)
2. Navigate Playwright to `http://localhost:8080/app.html`
3. Submit email → get session ID from `/tmp/ponderosa/sessions/` → navigate to magic link URL
4. Proceed through permissions → record (wait ≥20s for frames to accumulate) → finish

WebKit rejects self-signed certs — always use HTTP on port 8080, not HTTPS.

**The new user flow requires a session token in the URL.** The email request screen (`#screen-request`) calls `POST /session` to intake, which creates the token. In dev, read the token from `/tmp/ponderosa/sessions/` to construct the magic link manually.

## Deployment notes

Production server: **root@protean.io** — repo at `/root/ponderosa/`. Run `make install` from `site/` to deploy everything.

**HTTPS:** Let's Encrypt cert at `/etc/letsencrypt/live/ponderosafireprotection.com/` covers all subdomains (SAN). Add new subdomains with `certbot certonly --nginx -d <all names including new one>`.

**Services:** all installed to `/opt/ponderosa/<service>/`, run as `www-data`, venvs built with `/usr/bin/python3` (not pyenv — pyenv python under `/root/` is inaccessible to `www-data`).

**Mail:** Postfix configured as send-only (`inet_interfaces = loopback-only`). OpenDKIM signs outbound mail. `run.sh` in `site/` automates the full setup. DNS records required: SPF TXT at `@`, DKIM TXT at `mail._domainkey`, A record for each subdomain. PTR record set at Linode (VPS provider), not GoDaddy.
