# ponderosa-intake

HTTP API that receives video frames and trajectory data from the audit app client, persists them to disk, and signals the recommender to begin processing.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/survey/{survey_id}/image/{image_id}` | Upload a single JPEG frame |
| `POST` | `/survey/{survey_id}/trajectory` | Upload trajectory + email JSON; triggers recommender |
| `GET`  | `/health` | Liveness check |

The trajectory body is `{ surveyId, email, trajectory: [{frameId, lat, lon, alpha, beta, gamma}, …] }`. After writing `trajectory.json` and `email.txt` to the survey directory, intake opens the recommender FIFO and writes the survey ID.

## Directory layout

Each survey lands in its own subdirectory under `SURVEYS_DIR`:

```
$SURVEYS_DIR/
  <survey_id>/
    frames/
      1.jpg
      2.jpg
      …
    trajectory.json
    email.txt
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
| `RECOMMENDER_PIPE` | `/var/ponderosa/pipes/recommender` | FIFO to signal the recommender |
| `DEV` | `0` | Set to `1` to open CORS to all origins |

## Installation (production)

```sh
sudo make install
```

Installs to `/opt/ponderosa/intake/`, registers `ponderosa-intake.service` with systemd, and installs the nginx vhost config for `api.ponderosafireprotection.com`.
