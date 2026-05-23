# ponderosa-presenter

Daemon that reads survey IDs from a named pipe, renders a branded HTML report from `assessment.json`, writes it to the surveys web root, and sends the user a notification email.

## How it works

1. Reads a survey ID from `PRESENTER_PIPE` (blocking FIFO)
2. Loads `assessment.json` and `trajectory.json` from `$PROCESSED_DIR/<id>/`
3. Filters frames: keeps those with urgency above the mean, plus any below-mean frames whose actions aren't already covered by the above-mean set (novel-action rule)
4. Detects each frame's orientation (portrait vs landscape) using Pillow — selects the appropriate card layout
5. Renders `templates/report.html` via Jinja2 — overall rating pip display and summary at top, then one card per filtered frame with image, GPS metadata, Claude's assessment, and action tag pills
6. Copies frame JPEGs to `$SURVEYS_WEB/<id>/frames/` and writes `index.html`
7. If `trajectory.json` contains an email address, sends a notification via SMTP using `templates/email.html`

The notification email links to `$SURVEYS_URL/<id>/` — note the trailing slash, required for relative `frames/*.jpg` image paths in the report to resolve correctly.

## Templates

Both templates use Jinja2 with autoescaping and match the site's dark brand theme (charcoal backgrounds, orange `#e8611a` accents, Bebas Neue / Oswald / Inter type stack).

- `report.html` — full static report page served at `surveys.ponderosafireprotection.com/<id>/`. Cards use two layouts:
  - **Landscape** (default): image full-width on top, text below
  - **Portrait**: CSS grid `240px 1fr` with image on the left and text on the right; collapses to stacked on narrow screens
- `email.html` — table-based inline-style HTML email with a "VIEW YOUR REPORT" CTA button

## Running

```sh
./run.sh [--dev]
```

In `--dev` mode, surveys are read from `/tmp/ponderosa/surveys/processed`, the web root is `/tmp/ponderosa/surveys/web`, and `SURVEYS_URL` points to `http://localhost:8080`. SMTP still attempts to connect — expect a connection error if no local MTA is running.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROCESSED_DIR` | `/var/ponderosa/surveys/processed` | Source of completed surveys |
| `SURVEYS_WEB` | `/var/www/ponderosafireprotection.com/surveys` | Web root for generated pages |
| `PRESENTER_PIPE` | `/var/ponderosa/pipes/presenter` | FIFO read from recommender |
| `SURVEYS_URL` | `https://surveys.ponderosafireprotection.com` | Public base URL for email links |
| `SMTP_HOST` | `localhost` | SMTP server hostname |
| `SMTP_PORT` | `25` | SMTP server port |
| `SMTP_USER` | *(empty)* | SMTP username (triggers STARTTLS when set) |
| `SMTP_PASSWORD` | *(empty)* | SMTP password |
| `EMAIL_FROM` | `reports@ponderosafireprotection.com` | From address |

## Installation (production)

```sh
sudo make install
```

Installs to `/opt/ponderosa/presenter/`, registers `ponderosa-presenter.service` with systemd, and installs the nginx vhost config for `surveys.ponderosafireprotection.com`.
