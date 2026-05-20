# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Static marketing site for **Ponderosa Fire Protection** — a Colorado wildfire defense company. The entire site is a single self-contained HTML file with all CSS inlined in a `<style>` block. No framework, no build step, no JavaScript (beyond a tiny inline form-submit handler).

## Commands

All commands run from `site/`:

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
```

## Site architecture

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

## Deployment notes

The nginx vhost (`sites-available/ponderosafireprotection.com`) listens on port 80 only. TLS/HTTPS is not configured in this repo. Access and error logs go to `/var/log/nginx/ponderosafireprotection-{access,error}.log`.
