# ponderosa-presenter

Daemon that reads survey IDs from a named pipe, renders a branded HTML report from `assessment.json`, writes it to the surveys web root, and sends the user a notification email.

## How it works

1. Reads a survey ID from `PRESENTER_PIPE` (blocking FIFO)
2. Loads `assessment.json` and `trajectory.json` from `$PROCESSED_DIR/<id>/`
3. Renders `templates/report.html` via Jinja2 — one card per frame with the image, GPS metadata, Claude's assessment text, and action tag pills
4. Copies frame JPEGs to `$SURVEYS_WEB/<id>/frames/` and writes `index.html`
5. If `trajectory.json` contains an email address, sends a notification via SMTP using `templates/email.html`

## Templates

Both templates use Jinja2 with autoescaping and match the site's dark brand theme (charcoal backgrounds, orange `#e8611a` accents, Bebas Neue / Oswald / Inter type stack).

- `report.html` — full static report page served at `surveys.ponderosafireprotection.com/<id>/`
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
