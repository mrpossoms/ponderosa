# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

**Ponderosa Fire Protection** — a Colorado wildfire defense company. The repo contains two things:

1. **Marketing site** — static HTML/CSS in `site/`
2. **Property audit app** — a prototype AI-powered system that guides users through recording their property, analyzes footage with an LLM, and generates a personalized fire-risk report

## Commands

### Marketing site — run from `site/`

```sh
make serve    # local dev server at http://localhost:8000 (Python http.server)
make install  # symlink repo dirs into /etc/nginx and /var/www, reload nginx (requires root)
```

`make install` uses `ln -sf` to point system paths at the repo, so edits to `index.html` take effect immediately on the live nginx instance without re-running install.

## Structure

```
site/
  Makefile
  root/
    etc/nginx/sites-available/ponderosafireprotection.com   # nginx vhost config
    var/www/ponderosafireprotection.com/html/
      styles.css    # shared base styles (variables, reset, typography, buttons, brand, ember animation)
      index.html    # coming soon landing page
      home.html     # full marketing site

services/
  intake/           # Python package — RESTful API, receives frames + trajectory from client
  recommender/      # Python package — daemon, processes surveys through Claude, writes MD report
  presenter/        # Python package — daemon, converts MD report into HTML survey page

site/root/var/www/ponderosafireprotection.com/html/
  app.html          # audit app client (app.ponderosafireprotection.com)
```

### Service subdomains

- `ponderosafireprotection.com` — marketing site
- `app.ponderosafireprotection.com` — audit client app
- `api.ponderosafireprotection.com` — intake service
- `surveys.ponderosafireprotection.com/<id>` — generated survey report pages

### Audit app wizard screens (`app.html`)

1. **Intro** — splash with logo and "Get Started"
2. **Email** (`#screen-email`) — collects user email before permissions; stored in `userEmail` var
3. **Permissions** (`#screen-perms`) — requests camera, GPS, motion
4. **Record** (`#screen-record`) — live viewfinder, HUD with frame count + GPS status, record/finish buttons
5. **Upload** (`#screen-upload`) — indeterminate animated bar while frames are in-flight, switches to per-frame counter (`X / N`) as each settles, then "Finalizing…" for trajectory POST
6. **Done** (`#screen-done`) — success confirmation

### Audit app pipeline

1. Client (`app.html`) collects email, records video via `getUserMedia`, captures GPS + DeviceMotion data
2. Client scores frames client-side (variance of Laplacian on downsampled grayscale copy) and POSTs only sharp frames as JPEG to intake during recording (best-effort, tracked as promises)
3. On finish: waits for all in-flight frame POSTs, then POSTs trajectory + email as JSON
4. Intake stores frames, `trajectory.json` (includes email), and `email.txt` separately; signals recommender via named pipe
5. Recommender reads named pipe, passes each image + pose pair sequentially to Claude with a system prompt enumerating possible actions, generates a Markdown report
6. Recommender signals presenter via named pipe; presenter renders the MD into a static HTML page at `surveys/…/<id>`
7. User receives email with link to their survey page

### Inter-service communication

Named pipes (FIFOs) on the filesystem — intake → recommender → presenter. Work queue is a directory of survey subdirectories named by geohash survey ID.

## Site architecture (marketing)

`index.html` is the coming soon page: full-viewport centered layout with the shield/pine logo, brand name, and an animated ember particle effect. All styles are in a `<style>` block scoped to that page plus the shared `styles.css`.

`home.html` is the full marketing site organized as a single long page with anchor-linked sections in this order:

1. **Nav** — sticky, backdrop-blur, hides links/phone below 900px
2. **Hero** (`#top`) — two-column grid with animated ember dots (CSS keyframes) and an inline SVG scene
3. **Problem** (`#problem`) — statistics grid (4 columns → 2 on mobile)
4. **System** (`#system`) — four defense layers (2-col grid of `<article class="layer">`)
5. **Tiers** (`#tiers`) — three pricing cards on cream background; `.tier.featured` is elevated
6. **Process** (`#process`) — four-step grid
7. **Differentiator** — side-by-side comparison (`.diff-vs` with `.them` / `.us` columns)
8. **Partners** (`#partners`) — three partner cards
9. **Service area** (`#area`) — text + inline SVG Colorado map
10. **Testimonials** — three `.test` cards
11. **FAQ** (`#faq`) — native `<details>`/`<summary>` elements
12. **CTA / Form** (`#assess`) — contact form with inline `onsubmit` handler (no backend)
13. **Footer**

## CSS conventions

Shared base styles live in `styles.css`. Page-specific styles are in inline `<style>` blocks in each HTML file. CSS custom properties on `:root` (in `styles.css`) define the color palette:

- `--orange` / `--orange-deep` / `--ember` — brand fire tones
- `--black` / `--char` / `--char-2` — dark backgrounds
- `--cream` / `--paper` — light text and cream section backgrounds
- `--line` / `--line-strong` — subtle border alphas

Typography uses three Google Fonts: **Bebas Neue** (display headings), **Oswald** (labels/nav/UI text), **Inter** (body). Helper classes `.display`, `.oswald`, `.eyebrow` apply these.

Layout breakpoints are all inline via `@media(max-width:…)` adjacent to the component they affect — there is no separate mobile stylesheet.

## UI automation (Playwright MCP)

A Playwright MCP server is configured in `.mcp.json` so Claude can drive the app directly — navigate, click, screenshot, read the DOM — without a separate test harness.

**Setup:**
- MCP server: `npx @playwright/mcp` (config in `.mcp.json`)
- Browser: **WebKit** (Safari engine) with `--device "iPhone 15"` emulation
- Init script: `.claude/mock-camera.js` — injected into every page, mocks:
  - `getUserMedia` → canvas-based fake video stream (draws animated frames so the sharpness scorer works)
  - `DeviceMotionEvent.requestPermission` → auto-grants
  - `navigator.geolocation` → fixed Denver, CO coordinates

**To use:** start a plain HTTP dev server (`cd site/root/var/www/ponderosafireprotection.com/html && python3 -m http.server 8080`), then navigate Playwright to `http://localhost:8080/app.html`. WebKit rejects the self-signed dev cert so use HTTP on 8080, not the HTTPS server on 8000.

**Important:** Frame uploads happen during recording and complete very quickly on localhost. To test the upload progress screen, inject a `window.fetch` mock with a delay of at least 30s before navigating — shorter delays resolve before Playwright can screenshot the intermediate state.

The intake API calls (`/survey/*/image/*` and `/survey/*/trajectory`) hit `http://localhost:8001` in dev; run `cd services/intake && bash run.sh --dev` to start it locally.

## Deployment notes

Production server: **root@protean.io** — the repo lives at `/root/` (or the root home dir). Run `make install` from `site/` to deploy everything (site files + nginx + intake service + systemd unit).

**HTTPS:** All three nginx vhosts use Let's Encrypt certs:
- `ponderosafireprotection.com` + `www` → `/etc/letsencrypt/live/ponderosafireprotection.com/`
- `app.ponderosafireprotection.com` → `/etc/letsencrypt/live/ponderosafireprotection.com/` (same cert, SAN)
- `api.ponderosafireprotection.com` → `/etc/letsencrypt/live/ponderosafireprotection.com/` (same cert, SAN)

**Intake service:** installed to `/opt/ponderosa/intake/` with a venv at `.venv/` built using `/usr/bin/python3` (not pyenv — pyenv python lives under `/root/` which `www-data` can't access). Survey data lands in `/var/ponderosa/surveys/` owned by `www-data`.
