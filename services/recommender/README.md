# ponderosa-recommender

Daemon that reads survey IDs from a named pipe, calls the Claude API once per frame to assess wildfire risk, writes `assessment.json`, then signals the presenter.

## How it works

1. Reads a survey ID from `RECOMMENDER_PIPE` (blocking FIFO)
2. Loads all JPEGs from `$SURVEYS_DIR/<id>/frames/` and downsamples each so its largest dimension is ≤ 1024 px
3. Sends **all frames in a single API call** to `claude-haiku-4-5-20251001` — frames are interleaved with their pose data (lat, lon, heading, pitch, roll) as a sequence of image + text content blocks. Seeing the full survey at once lets the model calibrate urgency across frames rather than scoring each in isolation.
4. Parses the JSON array response: `[{ frame, urgency, assessment, actions[] }, …]`
5. Merges pose data back in and writes `assessment.json`
6. Moves the survey directory from `SURVEYS_DIR` to `PROCESSED_DIR`
7. Writes the survey ID to `PRESENTER_PIPE`

## System prompt

The prompt is assembled at startup from two files in `context/`:

- `SYSTEM.md` — role definition, output format, and assessment guidelines
- `ACTIONS.md` — enumeration of valid action codes (e.g. `TREE_PRUNING`, `BUILDING_VENTS`)

## Running

```sh
# Daemon mode (reads from FIFO)
./run.sh [--dev]

# Dev one-shot: process a single survey directory immediately
#   Makes a copy in /tmp; does not move or modify the original.
ANTHROPIC_API_KEY=sk-ant-… python main.py /path/to/survey_dir
```

Daemon mode in `--dev` uses `/tmp` paths instead of `/var/ponderosa`.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SURVEYS_DIR` | `/var/ponderosa/surveys/pending` | Where intake writes surveys |
| `PROCESSED_DIR` | `/var/ponderosa/surveys/processed` | Destination after processing |
| `RECOMMENDER_PIPE` | `/var/ponderosa/pipes/recommender` | FIFO read from intake |
| `PRESENTER_PIPE` | `/var/ponderosa/pipes/presenter` | FIFO written to presenter |
| `ANTHROPIC_API_KEY` | *(required)* | API key for Claude |

## Installation (production)

```sh
sudo make install
```

Installs to `/opt/ponderosa/recommender/`, registers `ponderosa-recommender.service` with systemd. The `ANTHROPIC_API_KEY` must be set in the service's environment before starting — edit the unit file or add a drop-in under `/etc/systemd/system/ponderosa-recommender.service.d/`.
