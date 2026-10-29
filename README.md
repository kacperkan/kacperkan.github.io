# [Hugo Academic CV Theme](https://github.com/HugoBlox/theme-academic-cv)

[![Screenshot](.github/preview.webp)](https://hugoblox.com/templates/)

The Hugo **Academic CV Template** empowers you to easily create your job-winning online resumé, showcase your academic publications, and create online courses or knowledge bases to grow your audience.

[![Get Started](https://img.shields.io/badge/-Get%20started-ff4655?style=for-the-badge)](https://hugoblox.com/templates/)
[![Discord](https://img.shields.io/discord/722225264733716590?style=for-the-badge)](https://discord.com/channels/722225264733716590/742892432458252370/742895548159492138)  
[![Twitter Follow](https://img.shields.io/twitter/follow/GetResearchDev?label=Follow%20on%20Twitter)](https://twitter.com/GetResearchDev)

️**Trusted by 250,000+ researchers, educators, and students.** Highly customizable via the integrated **no-code, Hugo Blox Builder**, making every site truly personalized ⭐⭐⭐⭐⭐

Easily write technical content with plain text Markdown, LaTeX math, diagrams, RMarkdown, or Jupyter, and import publications from BibTeX.

[Check out the latest demo](https://academic-demo.netlify.app/) of what you'll get in less than 10 minutes, or [get inspired by our academics and research groups](https://hugoblox.com/creators/).

The integrated [**Hugo Blox Builder**](https://hugoblox.com) and CMS makes it easy to create a beautiful website for free. Edit your site in the CMS (or your favorite editor), generate it with [Hugo](https://github.com/gohugoio/hugo), and deploy with GitHub or Netlify. Customize anything on your site with widgets, light/dark themes, and language packs.

- 👉 [**Get Started**](https://hugoblox.com/templates/)
- 📚 [View the **documentation**](https://docs.hugoblox.com/)
- 💬 [Chat with the **Hugo Blox Builder community**](https://discord.gg/z8wNYzb) or [**Hugo community**](https://discourse.gohugo.io)
- 🐦 Twitter: [@GetResearchDev](https://twitter.com/GetResearchDev) [@GeorgeCushen](https://twitter.com/GeorgeCushen) [#MadeWithHugoBlox](https://twitter.com/search?q=%23MadeWithHugoBlox&src=typed_query)
- ⬇️ **Automatically import your publications from BibTeX** with the [Hugo Academic CLI](https://github.com/GetRD/academic-file-converter)
- 💡 [Suggest an improvement](https://github.com/HugoBlox/hugo-blox-builder/issues)
- ⬆️ **Updating?** View the [Update Guide](https://docs.hugoblox.com/reference/update/) and [Release Notes](https://github.com/HugoBlox/hugo-blox-builder/releases)

## We ask you, humbly, to support this open source movement

Today we ask you to defend the open source independence of the Hugo Blox Builder and themes 🐧

We're an open source movement that depends on your support to stay online and thriving, but 99.9% of our creators don't give; they simply look the other way.

### [❤️ Click here to become a Sponsor, unlocking awesome perks such as _exclusive academic templates and blocks_](https://hugoblox.com/sponsor/)

<!--
<p align="center"><a href="https://hugoblox.com/templates/" target="_blank" rel="noopener"><img src="https://hugoblox.com/uploads/readmes/academic_logo_200px.png" alt="Hugo Academic Theme for Hugo Blox Builder"></a></p>
-->

## Demo image credits

- [Unsplash](https://unsplash.com)

## Latest news

<!--START_SECTION:news-->

- [Easily make an academic CV website to get more cites and grow your audience 🚀](https://hugoblox.com/blog/easily-make-academic-website/)
- [What&#39;s new in v5.2?](https://hugoblox.com/blog/whats-new-in-v5.2/)
- [What&#39;s new in v5.1?](https://hugoblox.com/blog/whats-new-in-v5.1/)
- [Version 5.0 (February 2021)](https://hugoblox.com/blog/version-5.0-february-2021/)
- [Version 5.0 Beta 3 (February 2021)](https://hugoblox.com/blog/version-5.0-beta-3-february-2021/)
<!--END_SECTION:news-->

## Gym Notes (`scripts/gym_note.py`)

Workout notes in `content/gym/` are generated from the current Google Sheets workout log and pCloud video links (`filedn.com`).

### Automatic Queue & Background Publishing

Queue a training week's plan date (`DD.MM.YYYY`) to automatically pull and publish `A`, `B`, and `C` notes as you finish them during the week:

```bash
# Queue a week date (installs/activates the macOS launchd agent and checks immediately)
pixi run gym-queue 10.10.2026

# Check queue status, A/B/C progress, launchd state, and recent sync log
pixi run gym-status

# Manually run a queue check & publish pass right now
pixi run gym-sync

# Remove a date from the queue (e.g. if a workout day was skipped)
pixi run gym-unqueue 10.10.2026
```

- **Schedule**: The macOS LaunchAgent (`~/Library/LaunchAgents/io.github.kacperkan.gym-note.plist`) runs every 30 minutes (and on wake) and logs to `~/.config/gym-note/sync.log`.
- **Setup**: Add a column named `Gotowe` (or `Gotowe?`) at the end of each workout tab (`A`, `B`, `C`). Select the cells below the header and choose **Insert → Checkbox** in Google Sheets. Keep the default checkbox values (`TRUE` / `FALSE`). Check a row only after entering all results and intended video links.
- **Readiness criteria**: A workout tab is published only when:
  1. The next un-noted row has its `Gotowe` checkbox checked. A missing column, blank cell, or unchecked checkbox blocks automatic publication.
  2. All planned exercise columns in that row have logged sets (`weights (reps)`). The `Gotowe` column is excluded from exercises.
  3. All referenced `filedn.com` `.mp4` videos are reachable and `ffmpeg` extracts their poster frames cleanly. Missing videos are retried on the next queue check. Exercises without video links are allowed; checking `Gotowe` confirms that the report is complete.
- **Auto-commit & cleanup**: Newly created notes under `content/gym/YYYY.MM.DD X/` are automatically committed and pushed to `main`. Once all three (`A`, `B`, `C`) exist for a date, it is automatically removed from `~/.config/gym-note/queue.json`.

### Manual / Single-Note Generation

Manual imports do not require a `Gotowe` column or a checked checkbox. They select the first unimported workout, just like the queue; an earlier row without results blocks later rows. Automatic tab selection requires exactly one unambiguous candidate. Already imported notes are not refreshed by the queue. To refresh one manually, provide its letter, plan date and `--force`; this overwrites only the same source, not a different workout.

```bash
# Auto-detect the only tab with an unimported workout
pixi run gym-note

# Specify day letter and/or plan date explicitly
pixi run gym-note C 10.10.2026

# Overwrite an existing note
pixi run gym-note B 10.10.2026 --force
```

### Source identity and migration

- Source identity is `(spreadsheet_id, sheet_id, workout_date)`, stored as a one-line JSON object in YAML frontmatter under `gym_source`. `workout_date` uses `YYYY-MM-DD` from the tab's `Data` cell. Row numbers and exercise results are not identifiers; repeated results are valid.
- The explicit plan date controls the existing directory/title and video paths, independently of the workout date. Without a plan-date argument, manual import uses the selected workout date; it never borrows another tab's row date.
- Queue dates are processed chronologically. Each tab selects its first unimported row in sheet order. Blank spacer rows are ignored; rows containing a date or exercise content require a valid, unique workout date. Missing/invalid/duplicate dates, disappeared imported dates, conflicting metadata and unresolved history block that tab with an explanation.
- `gym-status` shows local queue/launchd state plus the timestamp and results of the last synchronization in `~/.config/gym-note/last-sync.json`, explicitly a snapshot, not live Sheets data. Diagnostics use one-based Google Sheets row numbers and workout dates.
- Notes are staged separately; failed poster extraction leaves no completed note and preserves an existing note during `--force`. Imports use an exclusive process lock. Queue publication still uses the existing Git publishing workflow; use `--no-push` for local-only imports.

Historical migration requires explicit review and approval. First list the actual workbook/tab IDs and dated rows, then propose a mapping from each existing plan-date/letter directory to exactly one source. Exercise contents can support a proposal but never establish identity automatically. Copies of workbooks, repeated results and edited dates require manual resolution. Preserve exercise text, headings, comments, links and posters; insert only approved frontmatter metadata. Do not infer letters from tab positions: supported tab titles are `A`/`B`/`C` or `Day A`/`Day B`/`Day C`.

For the current cycle, 13 approved mappings were added to existing notes from plan dates `2026.09.26` through `2026.10.24`; older history remains unmigrated. Legacy notes preceding the earliest approved plan date for a tab remain historical. Legacy notes at or after that boundary block import. A workbook/tab without an approved mapping cannot silently replace a previously used source: review/migrate the relevant history before importing from it. New cycles therefore need an explicit source-mapping review, not an automatic reset. If an imported workout date changes or disappears, reconcile its existing metadata against the actual sheet before retrying; `--force` does not bypass this check.

