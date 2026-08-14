#!/usr/bin/env python3
"""Create a gym note in content/gym/ from a Google Sheets workout-log link.

Cell format in the sheet: classic cell_data, optionally followed (in any order) by
a comment in curly brackets and a YouTube link wrapped in @ signs, e.g.

    70/80/90 (5/5/5) <10/8/6> {ciezko poszlo} @https://youtube.com/shorts/xyz@

The comment goes to comment="", the link to link_data="", and both are stripped
from cell_data.

Usage (arguments in any order, all optional):
    python3 scripts/gym_note.py C 26.07.2026
    python3 scripts/gym_note.py B
    python3 scripts/gym_note.py "https://docs.google.com/spreadsheets/d/<id>/edit#gid=<gid>" [--force]

Spreadsheet: the pasted link if given, otherwise the newest "Workout ..."
spreadsheet found via the Drive API (most recently modified = current cycle).
Tab selection: the day letter (A/B/C) if given, else the #gid= fragment of the
link, else the tab whose last logged row is not yet present in any existing
note is picked automatically.
Row selection: the last logged row of the tab.
Note date: the DD.MM.YYYY argument, else the Data column of the selected row,
else tab A's date at the same row position (B/C share A's plan-week date).

Auth: OAuth (spreadsheets.readonly). Put the OAuth client file at
~/.config/gym-note/credentials.json (Google Cloud console -> APIs & Services ->
Credentials -> OAuth client ID, type "Desktop app", with the Google Sheets API
enabled). First run opens a browser; the token is cached at
~/.config/gym-note/token.json.

Dependencies: pip install google-api-python-client google-auth-oauthlib
"""

import argparse
import datetime
import re
import sys
from pathlib import Path

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]
CONFIG_DIR = Path.home() / ".config" / "gym-note"
ROOT = Path(__file__).resolve().parent.parent
GYM_DIR = ROOT / "content" / "gym"

LINK_RE = re.compile(r"@([^@]+)@")
COMMENT_RE = re.compile(r"\{([^}]*)\}")
LOGGED_RE = re.compile(r"^\d[\d.,/]*\s*\(")
SHEET_DATE_RE = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$")
SCHEME_RE = re.compile(r"\[\s*([^\],]+?)\s*(?:,[^\]]*)?\]")
HELPER_RE = re.compile(r"^[\d.,\s]+x\s*(?:\d+|max)$", re.IGNORECASE)
URL_ID_RE = re.compile(r"/spreadsheets/d/([a-zA-Z0-9_-]+)")
URL_GID_RE = re.compile(r"[#?&]gid=(\d+)")


def die(msg):
    sys.exit(f"error: {msg}")


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


def group_columns(header):
    """[(exercise name, [column indices])] — empty header cell continues the previous
    (merged) exercise column. Column 0 is the Data column."""
    groups = []
    for idx in range(1, len(header)):
        name = header[idx].strip()
        if name:
            groups.append((name, [idx]))
        elif groups:
            groups[-1][1].append(idx)
    return groups


def last_logged_row(rows, groups):
    """Index of the last row with at least one logged cell, or None."""
    found = None
    for i in range(1, len(rows)):
        for _, cols in groups:
            for c in cols:
                rest, _, _ = parse_cell(cell(rows[i], c))
                if LOGGED_RE.match(rest):
                    found = i
                    break
            else:
                continue
            break
    return found


def clean_name(name):
    return normalize(re.sub(r"\s*\[[^\]]*\]", " ", name))


def polish_weights(weights):
    return " ".join(w.replace(".", ",") for w in weights)


def load_summary(cell_data, helper):
    m = SCHEME_RE.search(cell_data)
    if m:
        return m.group(1)
    if helper:
        return normalize(helper)
    before = cell_data.split("(", 1)[0]
    weights = [w.strip() for w in before.split("/") if w.strip()]
    reps_m = re.search(r"\(([^)]*)\)", cell_data)
    reps = [r.strip() for r in reps_m.group(1).split("/")] if reps_m else []
    if reps and len(set(reps)) == 1 and weights:
        return f"{polish_weights(weights)}x{reps[0]}"
    if reps:
        return f"{len(reps)}x{reps[0]}"
    return ""


def extract_exercises(rows, row_idx, groups):
    """[(heading, cell_data, comment, link)] for the selected row."""
    exercises = []
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
        links = [l for p in parsed for l in p[2]]
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


def existing_cell_data():
    seen = set()
    for p in GYM_DIR.glob("*/index.md"):
        for cd in re.findall(r'cell_data="([^"]*)"', p.read_text(encoding="utf-8")):
            seen.add(normalize(cd))
    return seen


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


def main():
    ap = argparse.ArgumentParser(
        description="Create a gym note from the Google Sheets workout log.",
        epilog="Examples: gym_note.py C 26.07.2026 | gym_note.py B | gym_note.py <sheet url>",
    )
    ap.add_argument(
        "selector",
        nargs="*",
        help="any of, in any order: day letter A/B/C, note date DD.MM.YYYY, spreadsheet link",
    )
    ap.add_argument("--force", action="store_true", help="overwrite an existing note")
    ap.add_argument(
        "--credentials",
        type=Path,
        default=CONFIG_DIR / "credentials.json",
        help="OAuth client JSON (default: %(default)s)",
    )
    args = ap.parse_args()

    letter_arg = url = override_date = None
    for tok in args.selector:
        if "docs.google.com" in tok or URL_ID_RE.search(tok):
            url = tok
        elif SHEET_DATE_RE.match(tok):
            d, mo, y = (int(g) for g in SHEET_DATE_RE.match(tok).groups())
            override_date = datetime.date(y, mo, d)
        elif len(tok) == 1 and tok.isalpha():
            letter_arg = tok.upper()
        else:
            die(f"cannot interpret argument {tok!r} (expected A/B/C, DD.MM.YYYY, or a link)")

    creds = get_credentials(args.credentials)
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

    def tab_letter(pos):
        return chr(ord("A") + pos)

    if letter_arg is not None:
        pos = next(
            (i for i, t in enumerate(tabs) if t["title"].strip().upper() == letter_arg), None
        )
        if pos is None:
            pos = ord(letter_arg) - ord("A")
        if not 0 <= pos < len(tabs):
            die(f"no tab for letter {letter_arg} (spreadsheet has {len(tabs)} tabs)")
    elif gid is not None:
        pos = next((i for i, t in enumerate(tabs) if t["sheetId"] == gid), None)
        if pos is None:
            die(f"no tab with gid={gid} in this spreadsheet")
    else:
        seen = existing_cell_data()
        candidates = []
        for i, t in enumerate(tabs):
            rows = values[t["sheetId"]]
            if not rows:
                continue
            groups = group_columns(rows[0])
            li = last_logged_row(rows, groups)
            if li is None:
                continue
            row_data = [
                parse_cell(cell(rows[li], c))[0]
                for _, cols in groups
                for c in cols
                if LOGGED_RE.match(parse_cell(cell(rows[li], c))[0])
            ]
            if row_data and not any(normalize(cd) in seen for cd in row_data):
                candidates.append((i, t))
        if len(candidates) != 1:
            names = [f"{tab_letter(i)} ({t['title']})" for i, t in candidates] or ["none"]
            die(
                f"cannot auto-detect the tab — tabs with an un-noted logged row: "
                f"{', '.join(names)}. Pass a link with #gid=<tab gid>."
            )
        pos, _ = candidates[0]

    tab = tabs[pos]
    letter = letter_arg or tab_letter(pos)
    rows = values[tab["sheetId"]]
    if not rows:
        die(f"tab {letter} is empty")
    groups = group_columns(rows[0])
    row_idx = last_logged_row(rows, groups)
    if row_idx is None:
        die(f"tab {letter} has no logged rows")

    note_date = override_date or sheet_date(rows, row_idx)
    if note_date is None and pos != 0:
        note_date = sheet_date(values[tabs[0]["sheetId"]], row_idx)
    if note_date is None:
        die("cannot resolve the note date from the sheet — rerun with --date DD.MM.YYYY")

    exercises = extract_exercises(rows, row_idx, groups)
    if not exercises:
        die("selected row has no exercise cells")

    note_dir = GYM_DIR / f"{note_date:%Y.%m.%d} {letter}"
    note_path = note_dir / "index.md"
    if note_path.exists() and not args.force:
        die(f"{note_path} already exists — rerun with --force to overwrite")
    note_dir.mkdir(parents=True, exist_ok=True)
    note_path.write_text(build_note(note_date, letter, exercises), encoding="utf-8")

    print(f"created {note_path.relative_to(ROOT)}")
    for n, (heading, _, comment, link) in enumerate(exercises, 1):
        marks = []
        if comment:
            marks.append("comment")
        if link:
            marks.append("link")
        print(f"  {n}. {heading}" + (f"  [{' + '.join(marks)}]" if marks else "  [no comment/link]"))


if __name__ == "__main__":
    main()
