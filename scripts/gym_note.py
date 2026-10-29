#!/usr/bin/env python3
"""Create a gym note in content/gym/ from a Google Sheets workout-log link,
or queue a plan date to automatically pull and publish A/B/C notes as they become ready.

Cell format in the sheet: classic cell_data, optionally followed (in any order) by
a comment in curly brackets and a YouTube link wrapped in @ signs, e.g.

    70/80/90 (5/5/5) <10/8/6> {ciezko poszlo} @https://youtube.com/shorts/xyz@

The comment goes to comment="", the link to link_data="", and both are stripped
from cell_data.

Usage (arguments in any order, all optional):
    python3 scripts/gym_note.py C 26.07.2026
    python3 scripts/gym_note.py B
    python3 scripts/gym_note.py "https://docs.google.com/spreadsheets/d/<id>/edit#gid=<gid>" [--force]
    python3 scripts/gym_note.py --queue 10.10.2026
    python3 scripts/gym_note.py --status
    python3 scripts/gym_note.py --run-queue
    python3 scripts/gym_note.py --unqueue 10.10.2026

Spreadsheet: the pasted link if given, otherwise the newest "Workout ..."
spreadsheet found via the Drive API (most recently modified = current cycle).
Source identity and migration rules are documented in README.md.

Auth: OAuth (spreadsheets.readonly). Put the OAuth client file at
~/.config/gym-note/credentials.json (Google Cloud console -> APIs & Services ->
Credentials -> OAuth client ID, type "Desktop app", with the Google Sheets API
enabled). First run opens a browser; the token is cached at
~/.config/gym-note/token.json.

Dependencies: pip install google-api-python-client google-auth-oauthlib
"""

import argparse
import datetime
import fcntl
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]
CONFIG_DIR = Path.home() / ".config" / "gym-note"
QUEUE_PATH = CONFIG_DIR / "queue.json"
LOG_PATH = CONFIG_DIR / "sync.log"
SYNC_PATH = CONFIG_DIR / "last-sync.json"
LAUNCHD_LABEL = "io.github.kacperkan.gym-note"
LAUNCHD_PLIST = Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"
LAUNCHD_INTERVAL_SECONDS = 1800
LETTERS = ("A", "B", "C")
ROOT = Path(__file__).resolve().parent.parent
GYM_DIR = ROOT / "content" / "gym"
PCLOUD_ROOT = "https://filedn.com/lz7874DJjR0p3iQYiKf4iuF/Workouts"

LINK_RE = re.compile(r"@([^@]+)@")
COMMENT_RE = re.compile(r"\{([^}]*)\}")
LOGGED_RE = re.compile(r"^\d[\d.,/]*\s*\(")
SHEET_DATE_RE = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$")
ANNOTATION_RE = re.compile(r"\[([^\]]*)\]")
HELPER_RE = re.compile(r"^[\d.,\s]+x\s*(?:\d+|max)$", re.IGNORECASE)
WEIGHTS_RE = re.compile(r"\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)+")
SETS_RE = re.compile(r"^([\d.,/]+)\s*\(([^)]*)\)\s*(?:<([^>]*)>)?")
URL_ID_RE = re.compile(r"/spreadsheets/d/([a-zA-Z0-9_-]+)")
URL_GID_RE = re.compile(r"[#?&]gid=(\d+)")


def die(msg):
    sys.exit(f"error: {msg}")


def parse_date_str(tok):
    m = SHEET_DATE_RE.match(tok.strip())
    if not m:
        return None
    d, mo, y = (int(g) for g in m.groups())
    return datetime.date(y, mo, d)


def ensure_dot(text):
    """Comments are sentences — end them with a dot if no closing punctuation."""
    return text + "." if text and text[-1] not in ".!?…" else text


def parse_cell(raw):
    """Split a raw sheet cell into (cell_data, comments, links)."""
    links = [l.strip() for l in LINK_RE.findall(raw) if l.strip()]
    comments = [ensure_dot(c.strip()) for c in COMMENT_RE.findall(raw) if c.strip()]
    rest = COMMENT_RE.sub(" ", LINK_RE.sub(" ", raw))
    rest = re.sub(r"\s+", " ", rest).strip()
    return rest, comments, links


def normalize(s):
    return re.sub(r"\s+", " ", s).strip()


def cell(row, idx):
    return row[idx] if idx < len(row) else ""


def group_columns(header, max_cols=None):
    """[(exercise name, [column indices])] — empty header cell continues the previous
    (merged) exercise column. Column 0 is the Data column."""
    total = max(len(header), max_cols or 0)
    groups = []
    for idx in range(1, total):
        name = header[idx].strip() if idx < len(header) else ""
        if name.removesuffix("?").strip().casefold() == "gotowe":
            continue
        if name:
            groups.append((name, [idx]))
        elif groups and groups[-1][1][-1] == idx - 1:
            groups[-1][1].append(idx)
    return groups


def group_columns_for_rows(rows):
    if not rows:
        return []
    max_cols = max(len(r) for r in rows)
    return group_columns(rows[0], max_cols=max_cols)


def row_logged_cells(row, groups):
    """List of logged cell_data strings in a row."""
    return [
        parse_cell(cell(row, c))[0]
        for _, cols in groups
        for c in cols
        if LOGGED_RE.match(parse_cell(cell(row, c))[0])
    ]


def row_logged_group_count(row, groups):
    """Number of exercise groups in `row` that have at least one logged cell."""
    count = 0
    for _, cols in groups:
        if any(LOGGED_RE.match(parse_cell(cell(row, c))[0]) for c in cols):
            count += 1
    return count


def clean_name(name):
    return normalize(re.sub(r"\s*\[[^\]]*\]", " ", name))


def polish_weights(weights):
    return " ".join(w.replace(".", ",") for w in weights)


def load_summary(cell_data, helper):
    if helper:
        return normalize(helper)
    parts = [
        part
        for annotation in ANNOTATION_RE.findall(cell_data)
        for part in annotation.split(",")
        if HELPER_RE.fullmatch(part.strip()) or WEIGHTS_RE.fullmatch(part.strip())
    ]
    if parts:
        return ",".join(parts).strip()
    before = cell_data.split("(", 1)[0]
    weights = [w.strip() for w in before.split("/") if w.strip()]
    reps_m = re.search(r"\(([^)]*)\)", cell_data)
    reps = [r.strip() for r in reps_m.group(1).split("/")] if reps_m else []
    if reps and len(set(reps)) == 1 and weights:
        return f"{polish_weights(weights)}x{reps[0]}"
    if reps:
        return f"{len(reps)}x{reps[0]}"
    return ""


def extract_exercises(rows, row_idx, groups, note_date, letter):
    exercises = []
    video_root = f"{PCLOUD_ROOT}/{note_date:%d.%m.%Y}/{letter}"
    for name, cols in groups:
        raw_cells = [cell(rows[row_idx], c) for c in cols if cell(rows[row_idx], c).strip()]
        if not raw_cells:
            continue
        parsed = [parse_cell(rc) for rc in raw_cells]
        main = next((p for p in parsed if LOGGED_RE.match(p[0])), None)
        if main is None:
            main = next((p for p in parsed if p[0] and not HELPER_RE.match(p[0])), parsed[0])
        helper = next((p[0] for p in parsed if p is not main and HELPER_RE.match(p[0])), None)
        comments = [c for p in parsed for c in p[1]]
        links = [
            f"{video_root}/{quote(link)}.mp4" if re.fullmatch(r"[\w-]+", link) else link
            for p in parsed for link in p[2]
        ]
        sets = SETS_RE.match(main[0])
        if sets:
            counts = {
                label: len(values.split("/"))
                for label, values in zip(("weights", "reps", "reserve"), sets.groups())
                if values is not None
            }
            if len(set(counts.values())) > 1:
                details = ", ".join(f"{label}={count}" for label, count in counts.items())
                print(
                    f"warning: {clean_name(name)}: inconsistent set counts ({details})",
                    file=sys.stderr,
                )
        summary = load_summary(main[0], helper)
        heading = f"{clean_name(name)} {summary}".strip()
        exercises.append((heading, main[0], " ".join(comments), ", ".join(links)))
    return exercises


def sheet_date(rows, row_idx):
    m = SHEET_DATE_RE.match(cell(rows[row_idx], 0).strip()) if row_idx < len(rows) else None
    if m:
        d, mo, y = (int(g) for g in m.groups())
        return datetime.date(y, mo, d)
    return None


def source_key(source):
    if not isinstance(source, dict) or set(source) != {"spreadsheet_id", "sheet_id", "workout_date"}:
        raise ValueError("invalid gym_source metadata")
    if not isinstance(source["spreadsheet_id"], str) or not source["spreadsheet_id"] or type(source["sheet_id"]) is not int:
        raise ValueError("invalid spreadsheet/tab ID")
    if datetime.date.fromisoformat(source["workout_date"]).isoformat() != source["workout_date"]:
        raise ValueError("workout_date must use YYYY-MM-DD")
    return source["spreadsheet_id"], source["sheet_id"], source["workout_date"]


def note_sources():
    sources = {}
    legacy = []
    for path in sorted(GYM_DIR.glob("*/index.md")):
        text = path.read_text(encoding="utf-8")
        front = text.split("---", 2)[1] if text.startswith("---\n") else ""
        fields = re.findall(r"^gym_source: (.+)$", front, re.M)
        if not fields:
            if re.search(r"^gym_source\s*:", front, re.M):
                raise ValueError(f"{path}: gym_source must be a JSON object on one line")
            legacy.append(path)
            continue
        match = re.fullmatch(r"(\d{4}\.\d{2}\.\d{2}) ([ABC])", path.parent.name)
        if match is None:
            raise ValueError(f"{path}: invalid plan-date/letter directory")
        plan_date = datetime.datetime.strptime(match[1], "%Y.%m.%d").date()
        expected_title = f"title: {plan_date:%d.%m.%Y} – {match[2]}"
        if expected_title not in front.splitlines():
            raise ValueError(f"{path}: plan-date/letter conflicts with title")
        if len(fields) != 1:
            raise ValueError(f"{path}: duplicate gym_source metadata")
        try:
            key = source_key(json.loads(fields[0]))
        except (ValueError, TypeError) as exc:
            raise ValueError(f"{path}: invalid gym_source: {exc}") from exc
        if key in sources:
            raise ValueError(f"source assigned twice: {sources[key]} and {path}")
        sources[key] = path
    return sources, legacy


def source_for(tab, date):
    return {"spreadsheet_id": tab["spreadsheet_id"], "sheet_id": tab["sheetId"], "workout_date": date.isoformat()}


def select_source(tab, rows, sources, legacy, letter, target=None):
    groups = group_columns_for_rows(rows)
    candidates = []
    dates = set()
    for i, row in enumerate(rows[1:], 1):
        ready = any(str(cell(row, c)).strip().upper() == "TRUE" for c, name in enumerate(rows[0]) if name.strip().removesuffix("?").strip().casefold() == "gotowe")
        if not ready and not any(str(value).strip() for value in row[:1]) and not any(cell(row, c).strip() for _, cols in groups for c in cols):
            continue
        try:
            date = sheet_date(rows, i)
        except ValueError:
            date = None
        if date is None:
            raise ValueError(f"{letter}: Google Sheets row {i + 1}, date {cell(row, 0)!r}: missing/invalid workout date")
        if date in dates:
            raise ValueError(f"{letter}: Google Sheets row {i + 1}, date {date}: duplicate workout date")
        dates.add(date)
        candidates.append((i, source_for(tab, date)))
    bound = {key: path for key, path in sources.items() if key[:2] == (tab["spreadsheet_id"], tab["sheetId"])}
    missing = [key[2] for key in bound if datetime.date.fromisoformat(key[2]) not in dates]
    if missing:
        raise ValueError(f"{letter}: imported dates disappeared/changed: {', '.join(missing)}; resolve source mapping explicitly")
    if any(not path.parent.name.endswith(f" {letter}") for path in bound.values()):
        raise ValueError(f"{letter}: source tab assigned to a different note letter")
    if not bound and any(path.parent.name.endswith(f" {letter}") for path in sources.values()):
        raise ValueError(f"{letter}: workbook/tab changed; approve source mapping before import")
    related_legacy = [p for p in legacy if p.parent.name.endswith(f" {letter}")]
    if related_legacy:
        if not bound:
            raise ValueError(f"{letter}: unmapped history/new workbook; approve source mapping before import ({related_legacy[-1]})")
        first_plan = min(path.parent.name[:10] for path in bound.values())
        unresolved = [p for p in related_legacy if p.parent.name[:10] >= first_plan]
        if unresolved:
            raise ValueError(f"{letter}: unresolved historical mapping: {unresolved[0]}")
    if target is not None:
        assigned = next((key for key, path in bound.items() if path == target), None)
        if assigned is not None:
            return next((i, groups, source) for i, source in candidates if source_key(source) == assigned)
    for i, source in candidates:
        key = source_key(source)
        if key not in sources or sources[key] == target:
            return i, groups, source
    return None, groups, None


def write_note(note_date, letter, exercises, source, force=False):
    destination = note_dir_for(note_date, letter)
    if (destination / "index.md").exists() and not force:
        raise ValueError(f"{destination}: already exists; use --force for an explicit overwrite")
    GYM_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".gym-note-", dir=GYM_DIR) as tmp:
        staging = Path(tmp)
        if not save_posters(exercises, staging):
            raise ValueError("waiting: pCloud videos not all reachable for poster extraction")
        text = build_note(note_date, letter, exercises)
        text = text.replace("math: true\n", "math: true\ngym_source: " + json.dumps(source) + "\n", 1)
        (staging / "index.md").write_text(text, encoding="utf-8")
        if destination.exists():
            if not force:
                raise ValueError(f"{destination}: directory already exists; refusing overwrite")
            if (staging / "posters").exists():
                shutil.copytree(staging / "posters", destination / "posters", dirs_exist_ok=True)
            os.replace(staging / "index.md", destination / "index.md")
        else:
            os.rename(staging, destination)
    return destination


def get_credentials(creds_path):
    from google.auth.exceptions import RefreshError
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    token_path = CONFIG_DIR / "token.json"
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        if not set(SCOPES).issubset(set(creds.scopes or [])):
            creds = None  # scope set changed — force a fresh consent
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                creds = None  # token expired/revoked server-side — redo consent
        if not creds or not creds.valid:
            if not creds_path.exists():
                die(
                    f"no OAuth client file at {creds_path}. Create a 'Desktop app' "
                    "OAuth client in the Google Cloud console (Sheets API and "
                    "Drive API enabled) and save its JSON there."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def find_spreadsheet(creds):
    """Newest 'Workout ...' spreadsheet owned by the user (current training cycle)."""
    from googleapiclient.discovery import build

    drive = build("drive", "v3", credentials=creds)
    resp = (
        drive.files()
        .list(
            q=(
                "name contains 'Workout' and "
                "mimeType = 'application/vnd.google-apps.spreadsheet' and "
                "'me' in owners and trashed = false"
            ),
            orderBy="modifiedTime desc",
            pageSize=1,
            fields="files(id,name)",
        )
        .execute()
    )
    files = resp.get("files", [])
    if not files:
        die("no 'Workout' spreadsheet found in Drive — pass the link explicitly")
    print(f"spreadsheet: {files[0]['name']}")
    return files[0]["id"]


def escape(val):
    return val.replace('"', '\\"')


def build_note(note_date, letter, exercises):
    lines = [
        "---",
        f"title: {note_date:%d.%m.%Y} – {letter}",
        f"date: {datetime.date.today():%Y-%m-%d}",
        "math: true",
        "tags:",
        "    - Gym",
        "---",
        "",
    ]
    for n, (heading, cell_data, comment, link) in enumerate(exercises, 1):
        lines += [
            f"{n}. {heading}",
            "{{<",
            f'    exercise cell_data="{escape(cell_data)}"',
            f'    comment="{escape(comment)}"',
            f'    link_data="{escape(link)}"',
            ">}}",
            "",
        ]
    return "\n".join(lines)


def save_posters(exercises, note_dir):
    """Extract poster frames for all filedn.com .mp4 links. Returns True if all succeeded."""
    poster_dir = note_dir / "posters"
    all_ok = True
    for _, _, _, links in exercises:
        for link in re.split(r"[,|]", links):
            link = link.strip()
            if not link.startswith("https://filedn.com/") or not link.lower().split("?", 1)[0].endswith(".mp4"):
                continue
            filename = link.split("?", 1)[0].rsplit("/", 1)[-1]
            poster = poster_dir / f"{filename[:-4]}.jpg"
            if poster.exists():
                continue
            poster_dir.mkdir(exist_ok=True)
            try:
                subprocess.run(
                    ["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", "5", "-i", link,
                     "-frames:v", "1", "-vf", "scale=360:-2", "-q:v", "5", "-y", str(poster)],
                    check=True,
                    capture_output=True,
                    timeout=60,
                )
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                poster.unlink(missing_ok=True)
                all_ok = False
                print(f"warning: could not create poster for {filename}", file=sys.stderr)
    return all_ok


def note_dir_for(note_date, letter):
    return GYM_DIR / f"{note_date:%Y.%m.%d} {letter}"


def note_exists(note_date, letter):
    return (note_dir_for(note_date, letter) / "index.md").exists()


def load_queue():
    if not QUEUE_PATH.exists():
        return []
    try:
        data = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
        raw_dates = data.get("dates", [])
    except (json.JSONDecodeError, OSError):
        return []
    result = []
    for tok in raw_dates:
        d = parse_date_str(tok)
        if d and d not in result:
            result.append(d)
    return result


def save_queue(dates):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    unique = []
    for d in dates:
        if d not in unique:
            unique.append(d)
    payload = {
        "dates": [f"{d:%d.%m.%Y}" for d in unique],
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    QUEUE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def ensure_launchd_agent():
    """Install and load the macOS LaunchAgent to periodically run --run-queue."""
    if sys.platform != "darwin":
        return
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    LAUNCHD_PLIST.parent.mkdir(parents=True, exist_ok=True)
    python_bin = Path(sys.executable).resolve()
    env_path = f"{python_bin.parent}:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
    plist_data = {
        "Label": LAUNCHD_LABEL,
        "ProgramArguments": [str(python_bin), str(Path(__file__).resolve()), "--run-queue"],
        "WorkingDirectory": str(ROOT),
        "EnvironmentVariables": {
            "PATH": env_path,
            "HOME": str(Path.home()),
        },
        "StartInterval": LAUNCHD_INTERVAL_SECONDS,
        "RunAtLoad": False,
        "StandardOutPath": str(LOG_PATH),
        "StandardErrorPath": str(LOG_PATH),
    }
    new_bytes = plistlib.dumps(plist_data)
    changed = not LAUNCHD_PLIST.exists() or LAUNCHD_PLIST.read_bytes() != new_bytes
    if changed:
        LAUNCHD_PLIST.write_bytes(new_bytes)
    uid = os.getuid()
    domain_target = f"gui/{uid}/{LAUNCHD_LABEL}"
    check = subprocess.run(["launchctl", "print", domain_target], capture_output=True)
    if check.returncode != 0 or changed:
        subprocess.run(["launchctl", "bootout", f"gui/{uid}", str(LAUNCHD_PLIST)], capture_output=True)
        res = subprocess.run(["launchctl", "bootstrap", f"gui/{uid}", str(LAUNCHD_PLIST)], capture_output=True, text=True)
        if res.returncode == 0:
            print(f"launchd agent installed and active ({LAUNCHD_LABEL}, every {LAUNCHD_INTERVAL_SECONDS // 60} min)")
        else:
            print(f"warning: launchctl bootstrap returned {res.returncode}: {res.stderr.strip()}", file=sys.stderr)


def launchd_is_loaded():
    if sys.platform != "darwin":
        return False
    res = subprocess.run(
        ["launchctl", "print", f"gui/{os.getuid()}/{LAUNCHD_LABEL}"],
        capture_output=True,
    )
    return res.returncode == 0


def fetch_spreadsheet_tabs(creds, url=None):
    from googleapiclient.discovery import build

    svc = build("sheets", "v4", credentials=creds)
    gid = None
    if url:
        m = URL_ID_RE.search(url)
        if not m:
            die("cannot find a spreadsheet id in the link")
        spreadsheet_id = m.group(1)
        gid_m = URL_GID_RE.search(url)
        gid = int(gid_m.group(1)) if gid_m else None
    else:
        spreadsheet_id = find_spreadsheet(creds)
    meta = (
        svc.spreadsheets()
        .get(spreadsheetId=spreadsheet_id, fields="sheets(properties(sheetId,title,index))")
        .execute()
    )
    tabs = sorted((s["properties"] for s in meta["sheets"]), key=lambda p: p["index"])
    if not tabs:
        die("spreadsheet has no tabs")
    values = {}
    for t in tabs:
        resp = (
            svc.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=f"'{t['title']}'")
            .execute()
        )
        values[t["sheetId"]] = resp.get("values", [])
    for tab in tabs:
        tab["spreadsheet_id"] = spreadsheet_id
    return tabs, values, gid


def tab_letter(pos):
    return chr(ord("A") + pos)


def find_tab_pos(tabs, letter):
    matches = [i for i, t in enumerate(tabs) if t["title"].strip().upper() in (letter, f"DAY {letter}")]
    return matches[0] if len(matches) == 1 else None


def git_publish(created_dirs):
    """Commit and push newly created gym note directories."""
    if not created_dirs:
        return
    rel_paths = [str(d.relative_to(ROOT)) for d in created_dirs]
    msg = "add note" if len(rel_paths) == 1 else "add notes"
    try:
        subprocess.run(["git", "add", "--", *rel_paths], cwd=ROOT, check=True)
        subprocess.run(["git", "commit", "-m", msg, "--", *rel_paths], cwd=ROOT, check=True)
        push = subprocess.run(["git", "push"], cwd=ROOT, capture_output=True, text=True)
        if push.returncode != 0:
            subprocess.run(["git", "pull", "--rebase", "--autostash"], cwd=ROOT, check=True)
            subprocess.run(["git", "push"], cwd=ROOT, check=True)
        print(f"published to git ({msg}: {', '.join(rel_paths)})")
    except subprocess.CalledProcessError as exc:
        print(f"error: git publish failed: {exc}", file=sys.stderr)


def run_queue(creds_path, push=True):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    started = datetime.datetime.now().isoformat(timespec="seconds")
    SYNC_PATH.write_text(json.dumps({"started_at": started, "finished_at": None, "results": ["sync started"]}) + "\n")
    try:
        sync_queue(creds_path, push)
    except (Exception, SystemExit) as exc:
        SYNC_PATH.write_text(json.dumps({"results": [f"sync failed: {exc}"]}) + "\n")
        raise
    finally:
        snapshot = json.loads(SYNC_PATH.read_text())
        snapshot["started_at"] = started
        snapshot["finished_at"] = datetime.datetime.now().isoformat(timespec="seconds")
        if snapshot["results"] == ["sync started"]:
            snapshot["results"] = ["no pending dates"]
        SYNC_PATH.write_text(json.dumps(snapshot, indent=2) + "\n")


def sync_queue(creds_path, push=True):
    """Process queued dates: pull any complete A/B/C notes and publish to git."""
    dates = load_queue()
    if not dates:
        return
    pending_dates = sorted(d for d in dates if not all(note_exists(d, l) for l in LETTERS))
    if len(pending_dates) != len(dates):
        save_queue(pending_dates)
    if not pending_dates:
        print("all queued dates have A, B, C published — queue is now empty.")
        return

    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] checking queued dates: {', '.join(f'{d:%d.%m.%Y}' for d in pending_dates)}")
    creds = get_credentials(creds_path)
    tabs, values, _ = fetch_spreadsheet_tabs(creds)
    created_dirs = []
    messages = []
    try:
        sources, legacy = note_sources()
    except ValueError as exc:
        print(f"blocked: {exc}")
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        SYNC_PATH.write_text(json.dumps({"finished_at": datetime.datetime.now().isoformat(), "results": [str(exc)]}) + "\n")
        return

    for note_date in pending_dates:
        for letter in LETTERS:
            if note_exists(note_date, letter):
                print(f"  {note_date:%d.%m.%Y} {letter}: already published")
                continue
            pos = find_tab_pos(tabs, letter)
            if pos is None:
                messages.append(f"{note_date:%d.%m.%Y} {letter}: blocked (no unique matching tab in spreadsheet)")
                print(messages[-1])
                continue
            rows = values[tabs[pos]["sheetId"]]
            ready_idx = next(
                (i for i, name in enumerate(rows[0]) if name.strip().removesuffix("?").strip().casefold() == "gotowe"),
                None,
            ) if rows else None
            try:
                row_idx, groups, source = select_source(tabs[pos], rows, sources, legacy, letter)
            except ValueError as exc:
                messages.append(f"{note_date:%d.%m.%Y} {letter}: blocked: {exc}")
                print(messages[-1])
                continue
            logged_count = row_logged_group_count(rows[row_idx], groups) if row_idx is not None else 0
            total_groups = len(groups)
            detail = f"Google Sheets row {row_idx + 1}, date {source['workout_date']}" if source else "no unimported workout"
            messages.append(f"{note_date:%d.%m.%Y} {letter}: {detail}")
            if row_idx is None:
                messages[-1] += ": waiting (no unimported workout)"
                print(messages[-1])
                continue
            if ready_idx is None:
                messages[-1] += ": waiting (missing Gotowe checkbox column)"
                print(messages[-1])
                continue
            if str(cell(rows[row_idx], ready_idx)).strip().upper() != "TRUE":
                messages[-1] += ": waiting (Gotowe is not checked)"
                print(messages[-1])
                continue
            if logged_count < total_groups:
                messages[-1] += f": waiting ({logged_count}/{total_groups} exercise groups logged)"
                print(messages[-1])
                continue
            exercises = extract_exercises(rows, row_idx, groups, note_date, letter)
            try:
                note_dir = write_note(note_date, letter, exercises, source)
            except ValueError as exc:
                messages[-1] += f": {exc}"
                print(messages[-1])
                continue
            sources[source_key(source)] = note_dir / "index.md"
            created_dirs.append(note_dir)
            messages[-1] += f": created {note_dir.relative_to(ROOT)}"
            print(messages[-1])

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    SYNC_PATH.write_text(json.dumps({"finished_at": datetime.datetime.now().isoformat(), "results": messages}, indent=2) + "\n", encoding="utf-8")
    if created_dirs and push:
        git_publish(created_dirs)

    remaining = [d for d in pending_dates if not all(note_exists(d, l) for l in LETTERS)]
    if len(remaining) != len(pending_dates):
        save_queue(remaining)


def print_status():
    dates = load_queue()
    loaded = launchd_is_loaded()
    print(f"launchd agent ({LAUNCHD_LABEL}): {'active' if loaded else 'not loaded'}")
    if not dates:
        print("queue: empty")
    else:
        print("queue:")
        for d in dates:
            parts = [f"{l}={'done' if note_exists(d, l) else 'pending'}" for l in LETTERS]
            print(f"  {d:%d.%m.%Y}: {', '.join(parts)}")
    if SYNC_PATH.exists():
        try:
            snapshot = json.loads(SYNC_PATH.read_text(encoding="utf-8"))
            print(f"last sync snapshot (not live): {snapshot['finished_at']}")
            for result in snapshot["results"]:
                print(f"  {result}")
        except (ValueError, KeyError, TypeError):
            print("last sync snapshot: unreadable")
    else:
        print("last sync snapshot: unavailable (no sync recorded by this version)")
    if LOG_PATH.exists():
        lines = LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
        if lines:
            print(f"historical log (not live; {LOG_PATH}):")
            for line in lines[-6:]:
                print(f"  {line}")


def main():
    ap = argparse.ArgumentParser(
        description="Create a gym note from the Google Sheets workout log, or manage queued dates.",
        epilog=(
            "Examples: gym_note.py C 26.07.2026 | gym_note.py --queue 10.10.2026 | "
            "gym_note.py --status | gym_note.py --run-queue"
        ),
    )
    ap.add_argument(
        "selector",
        nargs="*",
        help="any of, in any order: day letter A/B/C, note date DD.MM.YYYY, spreadsheet link",
    )
    ap.add_argument("--force", action="store_true", help="overwrite an existing note")
    ap.add_argument(
        "--queue",
        action="store_true",
        help="queue the given DD.MM.YYYY date(s) to auto-publish A, B, C as they become ready",
    )
    ap.add_argument(
        "--unqueue",
        action="store_true",
        help="remove the given DD.MM.YYYY date(s) from the queue",
    )
    ap.add_argument(
        "--run-queue",
        action="store_true",
        help="check queued dates once and publish any newly completed A/B/C notes",
    )
    ap.add_argument(
        "--status",
        action="store_true",
        help="show queued dates, A/B/C completion status, and launchd agent status",
    )
    ap.add_argument(
        "--no-push",
        action="store_true",
        help="when running --queue or --run-queue, do not git commit/push created notes",
    )
    ap.add_argument(
        "--credentials",
        type=Path,
        default=CONFIG_DIR / "credentials.json",
        help="OAuth client JSON (default: %(default)s)",
    )
    args = ap.parse_args()

    if args.status:
        print_status()
        return

    if args.unqueue:
        to_remove = [parse_date_str(t) for t in args.selector]
        if not to_remove or any(d is None for d in to_remove):
            die("pass one or more DD.MM.YYYY dates with --unqueue")
        current = load_queue()
        updated = [d for d in current if d not in to_remove]
        save_queue(updated)
        print(f"removed {', '.join(f'{d:%d.%m.%Y}' for d in to_remove)} from queue")
        print_status()
        return

    if args.queue:
        to_add = [parse_date_str(t) for t in args.selector]
        if any(d is None for d in to_add):
            die("with --queue, arguments must be DD.MM.YYYY dates")
        current = load_queue()
        for d in to_add:
            if d not in current:
                current.append(d)
                print(f"queued {d:%d.%m.%Y}")
        save_queue(current)
        ensure_launchd_agent()
        run_queue(args.credentials, push=not args.no_push)
        return

    if args.run_queue:
        run_queue(args.credentials, push=not args.no_push)
        return

    letter_arg = url = override_date = None
    for tok in args.selector:
        if "docs.google.com" in tok or URL_ID_RE.search(tok):
            url = tok
        elif SHEET_DATE_RE.match(tok):
            override_date = parse_date_str(tok)
        elif len(tok) == 1 and tok.isalpha():
            letter_arg = tok.upper()
        else:
            die(f"cannot interpret argument {tok!r} (expected A/B/C, DD.MM.YYYY, or a link)")

    creds = get_credentials(args.credentials)
    tabs, values, gid = fetch_spreadsheet_tabs(creds, url)
    try:
        sources, legacy = note_sources()
    except ValueError as exc:
        die(str(exc))

    if letter_arg is not None:
        pos = find_tab_pos(tabs, letter_arg)
        if pos is None:
            die(f"no tab for letter {letter_arg} (spreadsheet has {len(tabs)} tabs)")
    elif gid is not None:
        pos = next((i for i, t in enumerate(tabs) if t["sheetId"] == gid), None)
        if pos is None:
            die(f"no tab with gid={gid} in this spreadsheet")
    else:
        candidates = []
        for i, t in enumerate(tabs):
            rows = values[t["sheetId"]]
            if not rows:
                continue
            letter = t["title"].strip().upper().removeprefix("DAY ")
            if letter not in LETTERS:
                continue
            try:
                li, _, _ = select_source(t, rows, sources, legacy, letter)
            except ValueError as exc:
                die(str(exc))
            if li is not None:
                candidates.append((i, t))
        if len(candidates) != 1:
            names = [f"{tab_letter(i)} ({t['title']})" for i, t in candidates] or ["none"]
            die(
                f"cannot auto-detect the tab — tabs with an un-noted logged row: "
                f"{', '.join(names)}. Pass a link with #gid=<tab gid>."
            )
        pos, _ = candidates[0]

    tab = tabs[pos]
    letter = letter_arg or tab["title"].strip().upper().removeprefix("DAY ")
    if letter not in LETTERS:
        die("selected tab has no unambiguous A/B/C letter")
    rows = values[tab["sheetId"]]
    if not rows:
        die(f"tab {letter} is empty")
    target = note_dir_for(override_date, letter) / "index.md" if override_date else None
    if args.force and target is None:
        die("--force requires an explicit plan date")
    try:
        row_idx, groups, source = select_source(tab, rows, sources, legacy, letter, target if args.force else None)
    except ValueError as exc:
        die(str(exc))
    if row_idx is None:
        die(f"tab {letter} has no unimported workout")
    if not row_logged_group_count(rows[row_idx], groups):
        die(f"Google Sheets row {row_idx + 1}, date {source['workout_date']}: waiting for logged results")
    if target and target.exists():
        assigned = next((key for key, path in sources.items() if path == target), None)
        if assigned != source_key(source):
            die("target has different/unmapped source; resolve metadata explicitly before --force")

    note_date = override_date or sheet_date(rows, row_idx)
    if note_date is None:
        die("cannot resolve the note date from the sheet — rerun with DD.MM.YYYY")

    exercises = extract_exercises(rows, row_idx, groups, note_date, letter)
    if not exercises:
        die("selected row has no exercise cells")

    try:
        note_dir = write_note(note_date, letter, exercises, source, args.force)
    except ValueError as exc:
        die(str(exc))
    print(f"created {note_dir.relative_to(ROOT)} (Google Sheets row {row_idx + 1}, date {source['workout_date']})")
    for n, (heading, _, comment, link) in enumerate(exercises, 1):
        marks = []
        if comment:
            marks.append("comment")
        if link:
            marks.append("link")
        print(f"  {n}. {heading}" + (f"  [{' + '.join(marks)}]" if marks else "  [no comment/link]"))


if __name__ == "__main__":
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with (CONFIG_DIR / "import.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            die("another gym-note process is running; retry after it finishes")
        main()
