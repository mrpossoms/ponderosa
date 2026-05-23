import json
import os
import secrets
import smtplib
from email.message import EmailMessage
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel, EmailStr

app = FastAPI(title="Ponderosa Intake")

_DEV = os.environ.get("DEV", "0") == "1"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _DEV else ["https://app.ponderosafireprotection.com"],
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)

SURVEYS_DIR      = Path(os.environ.get("SURVEYS_DIR",      "/var/ponderosa/surveys/pending"))
SESSIONS_DIR     = Path(os.environ.get("SESSIONS_DIR",     "/var/ponderosa/sessions"))
RECOMMENDER_PIPE = Path(os.environ.get("RECOMMENDER_PIPE", "/var/ponderosa/pipes/recommender"))
APP_URL          = os.environ.get("APP_URL",   "https://app.ponderosafireprotection.com")
SMTP_HOST        = os.environ.get("SMTP_HOST", "localhost")
SMTP_PORT        = int(os.environ.get("SMTP_PORT", "25"))
SMTP_USER        = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD    = os.environ.get("SMTP_PASSWORD", "")
EMAIL_FROM       = os.environ.get("EMAIL_FROM", "reports@ponderosafireprotection.com")

SURVEYS_DIR.mkdir(parents=True, exist_ok=True)
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

_jinja = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=select_autoescape(["html"]),
)


# ── Session management ────────────────────────────────────────────────────────

class SessionRequest(BaseModel):
    email: EmailStr


@app.post("/session", status_code=status.HTTP_204_NO_CONTENT)
async def create_session(body: SessionRequest):
    session_id = secrets.token_urlsafe(32)
    (SESSIONS_DIR / session_id).write_text(body.email)
    _send_magic_link(body.email, session_id)


def _session_email(session_id: str) -> str:
    """Return the email for a session, or raise 403 if invalid."""
    path = SESSIONS_DIR / session_id
    if not path.exists() or not _safe_path(path, SESSIONS_DIR):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid session")
    return path.read_text().strip()


def _send_magic_link(to: str, session_id: str) -> None:
    url = f"{APP_URL}?session={session_id}"
    html_body = _jinja.get_template("magic_link.html").render(url=url)
    text_body = (
        f"You're one step away from your property fire-risk assessment.\n\n"
        f"Open the audit app here:\n{url}\n\n"
        f"— Ponderosa Fire Protection"
    )

    msg = EmailMessage()
    msg["Subject"] = "Start Your Ponderosa Property Audit"
    msg["From"]    = EMAIL_FROM
    msg["To"]      = to
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            if SMTP_USER:
                s.starttls()
                s.login(SMTP_USER, SMTP_PASSWORD)
            s.send_message(msg)
    except Exception as exc:
        # Log but don't surface SMTP errors to the client
        print(f"SMTP error sending magic link to {to}: {exc}", flush=True)


# ── Survey upload ─────────────────────────────────────────────────────────────

def _validate_id(value: str) -> None:
    if not value.replace("-", "").replace("_", "").isalnum() or len(value) > 64:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid ID")


def _safe_path(path: Path, root: Path) -> bool:
    """Ensure path doesn't escape root via traversal."""
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


@app.post("/survey/{session_id}/image/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def upload_image(session_id: str, image_id: str, request: Request):
    _validate_id(image_id)
    _session_email(session_id)  # validates session exists

    body = await request.body()
    if not body:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty body")

    frames_dir = SURVEYS_DIR / session_id / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    (frames_dir / f"{image_id}.jpg").write_bytes(body)


@app.post("/survey/{session_id}/trajectory", status_code=status.HTTP_204_NO_CONTENT)
async def upload_trajectory(session_id: str, request: Request):
    email = _session_email(session_id)  # validates session and retrieves email

    body = await request.body()
    if not body:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty body")

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid JSON")

    sdir = SURVEYS_DIR / session_id
    sdir.mkdir(parents=True, exist_ok=True)

    # Attach email from session (don't rely on client-supplied value)
    data["email"] = email
    (sdir / "trajectory.json").write_text(json.dumps(data, indent=2))
    (sdir / "email.txt").write_text(email)

    _signal_recommender(session_id)


def _signal_recommender(session_id: str) -> None:
    if not RECOMMENDER_PIPE.exists():
        return
    try:
        fd = os.open(RECOMMENDER_PIPE, os.O_WRONLY | os.O_NONBLOCK)
        os.write(fd, (session_id + "\n").encode())
        os.close(fd)
    except OSError:
        pass


@app.get("/health")
def health():
    return {"ok": True}
