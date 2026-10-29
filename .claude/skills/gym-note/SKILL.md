---
name: gym-note
description: Import workout notes from Google Sheets or fill video links in existing notes. Use the repository importer and its source-identity checks; ask before resolving ambiguous historical mappings.
---

# Gym notes

Read `README.md` → Gym Notes before operating. Use the existing `pixi run gym-note`, `gym-queue`, `gym-status` and `gym-sync` entrypoints. Do not independently reconstruct row selection or infer letters from tab order.

Source identity is spreadsheet ID + tab ID + workout date, persisted in `gym_source` frontmatter. Exercise similarity is never proof that a workout was imported. Manual and queue imports select the first unimported source in sheet order. Missing/invalid/duplicate dates, metadata conflicts and unresolved history stop import rather than guessing.

The plan date controls the title, directory and video paths; it is not the workout date. Preserve existing paths. Manual refresh requires an explicit letter, plan date and `--force`, with the same source identity. Queue mode additionally requires `Gotowe`, results in every exercise group and successful poster extraction.

Historical migration is separate: inspect real source rows and existing notes, propose mappings and conflicts, obtain explicit approval, then add only approved metadata. Never rewrite historical exercise content without approval. A new workbook/tab requires source-mapping review when history exists. See README for the approved current-cycle migration boundary.

`gym-status` reports the last synchronization snapshot, not live Sheets data. Read its timestamp before reporting progress. Queue/sync can commit and push; do not run them without explicit publication permission. For verification, use isolated fixtures and mock external services/publication.

## Fill links

Use the explicitly selected note. If selection is ambiguous, ask. Preserve existing links, exercise data, headings and comments. Fill empty `link_data` slots in exercise order from the provided URLs, keeping URLs verbatim. Report fewer links than empty slots; stop and ask if there are more links than slots. Multiple clips in one slot use the existing comma-separated format only after approval.
