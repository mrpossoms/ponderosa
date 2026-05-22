# Services

Backend pipeline for the Ponderosa Fire Protection property audit app. Three cooperating daemons communicate through named-pipe FIFOs on the filesystem; no message broker or shared database is required.

## Pipeline

```
app.html (client)
    │  POST /survey/{id}/image/{n}   (JPEG frames, fire-and-forget during recording)
    │  POST /survey/{id}/trajectory  (pose data + email, on finish)
    ▼
┌─────────┐   FIFO: /var/ponderosa/pipes/recommender
│  intake │ ─────────────────────────────────────────►
└─────────┘                                           │
                                                      ▼
                                            ┌─────────────────┐   FIFO: /var/ponderosa/pipes/presenter
                                            │   recommender   │ ──────────────────────────────────────►
                                            └─────────────────┘                                       │
                                                                                                      ▼
                                                                                           ┌───────────────────┐
                                                                                           │     presenter     │
                                                                                           └───────────────────┘
                                                                                                    │
                                                                        surveys.ponderosafireprotection.com/<id>/
                                                                        + notification email to user
```

## Services

| Service | Description |
|---------|-------------|
| [intake](intake/) | FastAPI HTTP API — receives frames and trajectory from the client app |
| [recommender](recommender/) | Claude API daemon — assesses each frame for wildfire risk |
| [presenter](presenter/) | Jinja2 renderer — produces the HTML report page and sends the email |

## Filesystem layout (production)

```
/var/ponderosa/
  surveys/
    pending/          # intake writes here; recommender reads and moves out
      <survey_id>/
        frames/       # JPEG frames uploaded by client
        trajectory.json
        email.txt
    processed/        # recommender moves surveys here after assessment
      <survey_id>/
        frames/
        trajectory.json
        email.txt
        assessment.json   # per-frame Claude output
  pipes/
    recommender       # FIFO: intake → recommender
    presenter         # FIFO: recommender → presenter

/var/www/ponderosafireprotection.com/surveys/
  <survey_id>/
    index.html        # generated report page
    frames/           # copied from processed/
```

## Development

Each service has a `run.sh --dev` mode that redirects all paths to `/tmp/ponderosa/` and loosens access controls (open CORS on intake, local SMTP URLs in presenter). Start all three in separate terminals:

```sh
cd services/intake    && ./run.sh --dev
cd services/recommender && ANTHROPIC_API_KEY=sk-ant-… ./run.sh --dev
cd services/presenter && ./run.sh --dev
```

To test the recommender against a real survey without going through the full flow, pass a survey directory as a positional argument — it copies to `/tmp` and processes in place:

```sh
ANTHROPIC_API_KEY=sk-ant-… python services/recommender/main.py /path/to/survey_dir
```

## Installation (production)

From `site/`:

```sh
sudo make install
```

This runs `make install` in each service directory, which:
1. Creates a venv at `/opt/ponderosa/<service>/.venv` using `/usr/bin/python3`
2. Installs the package and dependencies
3. Provisions `/var/ponderosa/` with correct ownership (`www-data`)
4. Installs nginx vhost configs and enables them
5. Registers and enables the systemd unit

All three services run as `www-data`.
