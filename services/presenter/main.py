import json
import os
import smtplib
import stat
from email.message import EmailMessage
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

PROCESSED_DIR  = Path(os.environ.get("PROCESSED_DIR", "/var/ponderosa/surveys/processed"))
SURVEYS_WEB    = Path(os.environ.get("SURVEYS_WEB", "/var/www/ponderosafireprotection.com/surveys"))
PRESENTER_PIPE = Path(os.environ.get("PRESENTER_PIPE", "/var/ponderosa/pipes/presenter"))
SURVEYS_URL    = os.environ.get("SURVEYS_URL", "https://surveys.ponderosafireprotection.com")

SMTP_HOST      = os.environ.get("SMTP_HOST", "localhost")
SMTP_PORT      = int(os.environ.get("SMTP_PORT", "25"))
SMTP_USER      = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD  = os.environ.get("SMTP_PASSWORD", "")
EMAIL_FROM     = os.environ.get("EMAIL_FROM", "reports@ponderosafireprotection.com")

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_jinja = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    autoescape=select_autoescape(["html"]),
)


def ensure_pipe(path: Path) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        os.mkfifo(path)
    elif not stat.S_ISFIFO(path.stat().st_mode):
        raise RuntimeError(f"{path} exists but is not a FIFO")


def filter_assessments(assessments: list[dict]) -> list[dict]:
    urgencies = [a.get("urgency") or 0 for a in assessments]
    if not urgencies:
        return assessments
    mean = sum(urgencies) / len(urgencies)

    above = [a for a in assessments if (a.get("urgency") or 0) > mean]
    covered_actions = {action for a in above for action in (a.get("actions") or [])}

    novel = [
        a for a in assessments
        if (a.get("urgency") or 0) <= mean
        and any(action not in covered_actions for action in (a.get("actions") or []))
    ]

    included_ids = {a.get("frameId") for a in above + novel}
    return [a for a in assessments if a.get("frameId") in included_ids]


def render_html(survey_id: str, rating, summary: str, assessments: list[dict]) -> str:
    return _jinja.get_template("report.html").render(
        survey_id=survey_id,
        rating=rating,
        summary=summary,
        assessments=assessments,
    )


def present_survey(survey_id: str) -> str:
    """Render the HTML report and write it to the surveys web root. Returns the user's email."""
    survey_dir = PROCESSED_DIR / survey_id
    assessment = json.loads((survey_dir / "assessment.json").read_text())
    trajectory = json.loads((survey_dir / "trajectory.json").read_text())
    email      = trajectory.get("email", "")

    rating  = assessment.get("rating")
    summary = assessment.get("summary", "")
    frames  = assessment.get("frames", [])

    filtered = filter_assessments(frames)
    print(f"  {len(filtered)}/{len(frames)} frames included after urgency filter", flush=True)
    html = render_html(survey_id, rating, summary, filtered)

    out_dir = SURVEYS_WEB / survey_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Copy frames so the HTML can reference them relatively
    frames_src = survey_dir / "frames"
    frames_dst = out_dir / "frames"
    frames_dst.mkdir(exist_ok=True)
    for jpg in frames_src.glob("*.jpg"):
        (frames_dst / jpg.name).write_bytes(jpg.read_bytes())

    (out_dir / "index.html").write_text(html)
    return email


def send_email(to: str, survey_id: str) -> None:
    if not to:
        return

    url = f"{SURVEYS_URL}/{survey_id}/"
    html_body = _jinja.get_template("email.html").render(url=url)
    text_body = (
        f"Your property fire-risk report is ready.\n\n"
        f"View it here: {url}\n\n"
        f"— Ponderosa Fire Protection"
    )

    msg = EmailMessage()
    msg["Subject"] = "Your Ponderosa Fire Protection Property Report"
    msg["From"]    = EMAIL_FROM
    msg["To"]      = to
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        if SMTP_USER:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASSWORD)
        s.send_message(msg)


def process(survey_id: str) -> None:
    print(f"Presenting survey {survey_id}", flush=True)
    email = present_survey(survey_id)
    print(f"  Written to {SURVEYS_WEB / survey_id}", flush=True)
    if email:
        send_email(email, survey_id)
        print(f"  Email sent to {email}", flush=True)
    else:
        print("  No email address — skipping notification", flush=True)


def run() -> None:
    ensure_pipe(PRESENTER_PIPE)
    SURVEYS_WEB.mkdir(parents=True, exist_ok=True)

    print(f"Presenter listening on {PRESENTER_PIPE}", flush=True)

    while True:
        with open(PRESENTER_PIPE, "r") as pipe:
            for line in pipe:
                survey_id = line.strip()
                if not survey_id:
                    continue
                try:
                    process(survey_id)
                except Exception as exc:
                    print(f"ERROR presenting {survey_id}: {exc}", flush=True)


if __name__ == "__main__":
    run()
