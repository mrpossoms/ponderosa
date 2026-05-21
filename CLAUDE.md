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

### Audit app pipeline

1. Client (`app.html`) records video via `getUserMedia`, captures GPS + DeviceMotion data
2. Client scores frames client-side (variance of Laplacian on downsampled grayscale copy) and POSTs only sharp frames as JPEG to intake
3. Intake stores frames and trajectory, writes survey ID to a named pipe to trigger recommender
4. Recommender reads named pipe, passes each image + pose pair sequentially to Claude with a system prompt enumerating possible actions, generates a Markdown report
5. Recommender signals presenter via named pipe; presenter renders the MD into a static HTML page at `surveys/…/<id>`
6. User receives email with link to their survey page

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

A Playwright MCP server is configured in `.claude/settings.json` so Claude can drive the app directly — navigate, click, screenshot, read the DOM — without a separate test harness.

**Setup:**
- MCP server: `npx @playwright/mcp` (no install needed)
- Browser: Chrome with `--device "iPhone 15"` emulation and `--ignore-https-errors`
- Init script: `.claude/mock-camera.js` — injected into every page, mocks:
  - `getUserMedia` → canvas-based fake video stream (draws animated frames so the sharpness scorer works)
  - `DeviceMotionEvent.requestPermission` → auto-grants
  - `navigator.geolocation` → fixed Denver, CO coordinates

**To use:** start the dev server (`make serve` in `site/`), then ask Claude to interact with `https://localhost:8000/app.html`. The Playwright tools will be available in the session after restarting Claude Code with the project open.

The intake API calls (`/survey/*/image/*` and `/survey/*/trajectory`) hit `http://localhost:8001` in dev; if the intake service isn't running, frame POSTs fail silently (best-effort) and the trajectory POST will show an upload error on the done screen.

## Deployment notes

The nginx vhost (`sites-available/ponderosafireprotection.com`) listens on port 80 only. TLS/HTTPS is not configured in this repo. Access and error logs go to `/var/log/nginx/ponderosafireprotection-{access,error}.log`.
