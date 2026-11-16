# CLAUDE.md

## project overview
personal Hugo Academic CV site (`kacperkan.github.io`) and workout-note automation
- `content/`, `config/`, `layouts/`, `assets/`, `static/`: Hugo Blox site sources and overrides
- `scripts/gym_note.py`: Google Sheets workout-note importer and `launchd` queue publisher (`content/gym/`, `.claude/skills/gym-note/SKILL.md`, `README.md` → Gym Notes)

## rules
- never commit changes unless the user explicitly asks
- never add "Co-Authored-By" lines to commits
- never store credentials, API keys, tokens, or account IDs in tracked files (code, scripts, or docs); load them exclusively from `~/.config/gym-note/`, `.env`, or environment variables

## code style
- use the `ponytail` skill (`full` level by default) on coding tasks
- prefer single-line code when it stays readable; avoid splitting logic across many lines unless the line would become extremely long
- never write one-line compound statements: the body of an `if`/`elif`/`else`/`for`/`while`/`try`/`except`/`with` must go on its own indented line (e.g. not `if x: return`)
- prefer avoiding blank lines within function/method bodies
- use 1 blank line between methods/nested functions, and 2 blank lines between top-level functions/classes
- use 1 blank line between external package imports and local imports
- prefer lowercase style, except class names which use PascalCase
- use double quotation marks for strings
- do not add comments unless asked
- match the existing codestyle when making changes
- solve the whole problem with the least new code; reuse existing codebase helpers/patterns first, then stdlib/platform features, then installed dependencies before writing new code, and never add a dependency for a few lines
- before editing, trace every caller/config/export the change reaches; for bug fixes, grep every caller and fix the root cause once in shared code
- deletion beats addition; keep values in native shapes and avoid unrequested abstractions, wrappers, type conversions, options, or boilerplate
- preserve validation at trust boundaries, error handling, security, accessibility, and operational contracts when moving, merging, or simplifying code
- end coding replies with 1–2 lines stating what was skipped/not checked and any user-facing risk

## python
- package & task manager: `pixi` (`pixi.toml`)
- run tasks and Python commands with `pixi run` (e.g. `pixi run gym-status`, `pixi run test-gym-note`, `pixi run python ...`)

## user edits
- the user may edit code between messages; prefer keeping their changes

## updating CLAUDE.md
- when making changes, check whether `CLAUDE.md` needs updating with new context
- describe the current logic as it stands now, not as a delta from previous behavior; avoid historical phrasing like "now uses", "changed from", "no longer", "used to", "instead of"
- keep CLAUDE.md brief
