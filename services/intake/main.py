import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Ponderosa Intake")

_DEV = os.environ.get("DEV", "0") == "1"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _DEV else ["https://app.ponderosafireprotection.com"],
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)

SURVEYS_DIR  = Path(os.environ.get("SURVEYS_DIR", "/var/ponderosa/surveys"))
RECOMMENDER_PIPE = Path(os.environ.get("RECOMMENDER_PIPE", "/var/ponderosa/pipes/recommender"))

SURVEYS_DIR.mkdir(parents=True, exist_ok=True)


def survey_dir(survey_id: str) -> Path:
    _validate_id(survey_id)
    return SURVEYS_DIR / survey_id


def _validate_id(value: str) -> None:
    if not value.replace("-", "").replace("_", "").isalnum() or len(value) > 64:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid ID")


@app.post("/survey/{survey_id}/image/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def upload_image(survey_id: str, image_id: str, request: Request):
    _validate_id(image_id)

    body = await request.body()
    if not body:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty body")

    frames_dir = survey_dir(survey_id) / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    dest = frames_dir / f"{image_id}.jpg"
    dest.write_bytes(body)


@app.post("/survey/{survey_id}/trajectory", status_code=status.HTTP_204_NO_CONTENT)
async def upload_trajectory(survey_id: str, request: Request):
    body = await request.body()
    if not body:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty body")

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid JSON")

    sdir = survey_dir(survey_id)
    sdir.mkdir(parents=True, exist_ok=True)
    (sdir / "trajectory.json").write_text(json.dumps(data, indent=2))

    if email := data.get("email"):
        (sdir / "email.txt").write_text(str(email))

    _signal_recommender(survey_id)


def _signal_recommender(survey_id: str) -> None:
    if not RECOMMENDER_PIPE.exists():
        return
    try:
        fd = os.open(RECOMMENDER_PIPE, os.O_WRONLY | os.O_NONBLOCK)
        os.write(fd, (survey_id + "\n").encode())
        os.close(fd)
    except OSError:
        pass  # recommender not listening yet; survey stays on disk for later pickup


@app.get("/health")
def health():
    return {"ok": True}
