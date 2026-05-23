import argparse
import base64
import io
import json
import os
import shutil
import stat
import tempfile
from pathlib import Path

import anthropic
from PIL import Image

SURVEYS_DIR      = Path(os.environ.get("SURVEYS_DIR", "/var/ponderosa/surveys/pending"))
PROCESSED_DIR    = Path(os.environ.get("PROCESSED_DIR", "/var/ponderosa/surveys/processed"))
RECOMMENDER_PIPE = Path(os.environ.get("RECOMMENDER_PIPE", "/var/ponderosa/pipes/recommender"))
PRESENTER_PIPE   = Path(os.environ.get("PRESENTER_PIPE", "/var/ponderosa/pipes/presenter"))

_CONTEXT_DIR = Path(__file__).parent / "context"
_SYSTEM_PROMPT = (
    (_CONTEXT_DIR / "SYSTEM.md").read_text()
    + "\n"
    + (_CONTEXT_DIR / "ACTIONS.md").read_text()
)

_client = anthropic.Anthropic(timeout=120.0)


def ensure_pipe(path: Path) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        os.mkfifo(path)
    elif not stat.S_ISFIFO(path.stat().st_mode):
        raise RuntimeError(f"{path} exists but is not a FIFO")

def _sanitize_json(text: str) -> str:
    return "\n".join(l for l in text.split("\n") if "```" not in l)


def _encode_image(frame_path: Path) -> str:
    img = Image.open(frame_path)
    if max(img.size) > 1024:
        img.thumbnail((1024, 1024), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return base64.standard_b64encode(buf.getvalue()).decode()


def assess_all_frames(frames: list[tuple[int, Path, dict]]) -> list[dict]:
    """Single API call covering all frames. Returns list of assessment dicts."""
    content = []
    for frame_id, frame_path, pose in frames:
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/jpeg", "data": _encode_image(frame_path)},
        })
        content.append({
            "type": "text",
            "text": (
                f"Frame {frame_id} — "
                f"lat: {pose.get('lat')}, lon: {pose.get('lon')}, "
                f"heading: {pose.get('alpha')}°, "
                f"pitch: {pose.get('beta')}°, "
                f"roll: {pose.get('gamma')}°"
            ),
        })

    response = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )

    try:
        return json.loads(_sanitize_json(response.content[0].text))
    except json.JSONDecodeError:
        return {}


def process_survey(survey_dir: Path) -> None:
    frames_dir = survey_dir / "frames"
    trajectory = json.loads((survey_dir / "trajectory.json").read_text())

    pose_by_frame = {entry["frameId"]: entry for entry in trajectory["trajectory"]}

    frame_paths = sorted(frames_dir.glob("*.jpg"), key=lambda p: int(p.stem))
    frames = [(int(p.stem), p, pose_by_frame.get(int(p.stem), {})) for p in frame_paths]

    print(f"  Assessing {len(frames)} frames in a single call", flush=True)
    result = assess_all_frames(frames)

    pose_index = {frame_id: pose for frame_id, _, pose in frames}
    frame_assessments = [
        {"frameId": r.get("frame"), "pose": pose_index.get(r.get("frame"), {}), **r}
        for r in result.get("frames", [])
    ]

    assessment = {
        "rating":  result.get("rating"),
        "summary": result.get("summary", ""),
        "frames":  frame_assessments,
    }
    (survey_dir / "assessment.json").write_text(json.dumps(assessment, indent=2))


def move_to_processed(survey_id: str) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    (SURVEYS_DIR / survey_id).rename(PROCESSED_DIR / survey_id)


def dev_process(survey_path: Path) -> None:
    """Copy survey_path to /tmp, process it in place, and print the report location."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="ponderosa-", suffix=f"-{survey_path.name}"))
    work_dir = tmp_dir / survey_path.name
    shutil.copytree(survey_path, work_dir)
    print(f"Copied survey to {work_dir}", flush=True)
    process_survey(work_dir)
    # report = work_dir / "report.md"
    # print(f"\nReport written to {report}", flush=True)
    # print("-" * 60, flush=True)
    # print(report.read_text(), flush=True)


def signal_presenter(survey_id: str) -> None:
    try:
        fd = os.open(PRESENTER_PIPE, os.O_WRONLY | os.O_NONBLOCK)
        os.write(fd, (survey_id + "\n").encode())
        os.close(fd)
    except OSError:
        pass  # presenter not listening; survey stays on disk for later pickup


def run() -> None:
    ensure_pipe(RECOMMENDER_PIPE)

    print(f"Recommender listening on {RECOMMENDER_PIPE}", flush=True)

    with open(RECOMMENDER_PIPE, "r") as pipe:
        for line in pipe:
            survey_id = line.strip()
            if not survey_id:
                continue
            print(f"Processing survey {survey_id}", flush=True)
            try:
                process_survey(SURVEYS_DIR / survey_id)
                move_to_processed(survey_id)
                signal_presenter(survey_id)
            except Exception as exc:
                print(f"ERROR processing {survey_id}: {exc}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ponderosa Recommender")
    parser.add_argument(
        "survey",
        nargs="?",
        metavar="SURVEY_DIR",
        help="Path to a survey directory to process immediately (dev mode). "
             "A copy is made in /tmp; the original is not modified.",
    )
    args = parser.parse_args()

    if args.survey:
        dev_process(Path(args.survey).expanduser().resolve())
    else:
        run()
