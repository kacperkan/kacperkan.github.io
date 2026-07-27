---
name: gym-note
description: Create a gym note in content/gym/ from the Google Sheets workout log. Reads the newest "Workout on ..." spreadsheet, finds the row for the given date (default today), and generates the note with exercise shortcodes — cell_data filled in, comment and link_data left empty for manual fill. Use when the user asks to create/import today's gym note, workout note, or fill in training data from the sheet.
---

# Gym note from Google Sheets

Generate `content/gym/YYYY.MM.DD X/index.md` from the workout spreadsheet.

**Model economy:** this task is mechanical — do NOT run it on an expensive model. Delegate the whole flow (steps 1–5) to a single `general-purpose` subagent via the Agent tool with `model: "haiku"`, passing these instructions and the arguments verbatim in the prompt. Run synchronously (`run_in_background: false`), relay its report. If the Haiku run misparses the sheet (wrong tab, mismapped columns), retry once with `model: "sonnet"`. Only run inline if the Agent tool is unavailable.

Arguments (all optional): `[date] [day-letter]`
- `date` — actual workout date, used only for the note title and folder name; default: today. (Row selection does not use it — see step 3.)
- `day-letter` — A/B/C (sheet tab); default: auto-detect (see step 3).

## Steps

### 1. Load Google Drive tools

Load via ToolSearch: `select:mcp__claude_ai_Google_Drive__search_files,mcp__claude_ai_Google_Drive__read_file_content`.
If Drive MCP is unavailable or unauthenticated, tell the user to reconnect the Google Drive connector and stop.

### 2. Find the spreadsheet

Search: `title contains 'Workout' and mimeType = 'application/vnd.google-apps.spreadsheet' and owner = 'me'`.
Titles look like "Workout on 26.07.2026" — each spreadsheet is a training cycle. Pick the one with the most recent `modifiedTime` (that is the current cycle). Then read it with `read_file_content`.

### 3. Parse the tab and row

`read_file_content` renders the spreadsheet as one markdown table per tab, **in tab order but without tab names** — first table = A, second = B, third = C. (The `search_files` content snippet does show tab names like `# A` if you need to confirm.)

Each table:
- Header row: `Data`, then exercise names. Merged cells repeat the name with a `\[merged\]` prefix — collapse consecutive duplicates into one exercise column.
- Data rows: optional date in the `Data` column (`D.MM.YYYY` / `DD.MM.YYYY`), then cells per exercise.

**The `Data` column date is the plan-week date, NOT the actual workout date** — do not trust it for matching. Select the row like this:
1. A row is "logged" if its cells match the cell_data pattern `weights (reps)`, e.g. `40/45/50/55/60 (5/5/5/5/5) <10/10/7/5/4> [5x5, ...]`. Plan-only rows (just `[3x10, 17.5/22.5/27.5]`) are not logged.
2. If a day-letter was given: take the last logged row of that tab.
3. Otherwise: for each tab, take its last logged row and check whether that row's cell_data already appears in an existing note under `content/gym/` — the tab whose last logged row is NOT yet in any note is the target, and determines the letter. If several qualify or none do, tell the user what you found and ask.

**Cell mapping caveats:**
- A merged exercise column holds two cells: the cell_data one and a helper cell with spaced weights like `40 45 50 55 60x5` (Polish decimal commas). Skip helper cells — take the cell matching the cell_data pattern.
- Map cells to exercise names positionally after collapsing merged headers.

### 4. Write the note

Path: `content/gym/YYYY.MM.DD X/index.md` (e.g. `content/gym/2026.07.26 A/index.md`). If it already exists, show it and ask before overwriting.

Frontmatter (title = workout date, date = today):

```markdown
---
title: DD.MM.YYYY – X
date: <today, YYYY-MM-DD>
math: true
tags:
    - Gym
---
```

Then each exercise, numbered in column order, blank line between blocks:

```
N. <Exercise name from header> <load summary>
{{<
    exercise cell_data="<cell verbatim from sheet>"
    comment=""
    link_data=""
>}}
```

- `cell_data`: the sheet cell verbatim.
- `comment` and `link_data`: always empty strings — the user fills these manually.
- Load summary in the heading:
  - If the cell has a `[NxM]` / `[Nx max]` scheme bracket: use just the scheme, e.g. `Podciąganie na drążku nachwytem 5x5` (drop anything after a comma inside the bracket).
  - Otherwise: spaced weights with Polish decimal commas + `x` + the (uniform) rep count, e.g. `Wyciskanie leżąc wąskim chwytem 50 57,5 62,5 67,5 72,5x6`. Weight `0` stays `0`.
  - Non-uniform reps and no scheme: follow the closest precedent in existing notes; when in doubt use `NxM` from the first set count.
- Strip any surrounding exercise-name annotations in square brackets from the header name when they are coaching notes (match how previous notes titled the same exercise — check an older note for that exercise if unsure).

### 5. Verify

Compare against the most recent existing note in `content/gym/` for format drift (frontmatter, spacing, numbering). Report the created path and list the exercises so the user can fill comments and video links.

Note: in existing notes a heading may deliberately disagree with its cell_data — the sheet is coach-written and sometimes has typos; the user corrects the heading by hand and keeps cell_data verbatim. Never "fix" such mismatches in existing notes, and don't treat them as format drift.
