# ponderosa-intake

HTTP API that receives video frames and trajectory data from the audit app client, persists them to disk, and signals the recommender to begin processing.

## Session-based authentication

Before uploading anything, the client requests a session by POSTing an email address. Intake sends a magic-link email containing `APP_URL?session=<token>`. The user clicks the link, the app extracts the session ID from the query string, and includes it in every subsequent upload request. Intake validates the session on each request; unknown session IDs are rejected with 403.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/session` | Request a session — body: `{ "email": "user@example.com" }`. Sends magic link. Returns 204. |
| `POST` | `/survey/{session_id}/image/{image_id}` | Upload a single JPEG frame (session validated) |
| `POST` | `/survey/{session_id}/trajectory` | Upload trajectory JSON; triggers recommender. Returns 204. |
| `GET`  | `/health` | Liveness check |

The trajectory body is `{ surveyId, trajectory: [{frameId, lat, lon, alpha, beta, gamma}, …] }`. The email address is pulled server-side from the session file, not trusted from the client.

## Directory layout

Each survey lands under `SURVEYS_DIR` keyed by session ID:

```
$SURVEYS_DIR/
  <session_id>/
    frames/
      1.jpg
      2.jpg
      …
    trajectory.json
    email.txt
```

Sessions are stored as files containing the email address:

```
$SESSIONS_DIR/
  <session_id>      # file contents: user@example.com
```

## Running

```sh
# Dev (hot-reload, open CORS, /tmp paths)
./run.sh --dev

# Production (started by systemd)
./run.sh
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SURVEYS_DIR` | `/var/ponderosa/surveys/pending` | Root for incoming survey data |
| `SESSIONS_DIR` | `/var/ponderosa/sessions` | Session token files |
| `RECOMMENDER_PIPE` | `/var/ponderosa/pipes/recommender` | FIFO to signal the recommender |
| `APP_URL` | `https://app.ponderosafireprotection.com` | Base URL for magic links |
| `SMTP_HOST` | `localhost` | SMTP server for sending magic links |
| `SMTP_PORT` | `25` | SMTP port |
| `EMAIL_FROM` | `reports@ponderosafireprotection.com` | From address for magic link emails |
| `DEV` | `0` | Set to `1` to open CORS to all origins |

## Installation (production)

```sh
sudo make install
```

Installs to `/opt/ponderosa/intake/`, provisions `/var/ponderosa/sessions` (owned by `www-data`), registers `ponderosa-intake.service` with systemd, and installs the nginx vhost config for `api.ponderosafireprotection.com`.
