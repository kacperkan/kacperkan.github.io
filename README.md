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
- **Readiness criteria**: A workout tab (`A`, `B`, or `C`) is published only when:
  1. All planned exercise columns in the next un-noted row have logged sets (`weights (reps)`).
  2. Video links (`@1@`, `@2@`, ...) are present in the row.
  3. All referenced `filedn.com` `.mp4` videos are reachable and `ffmpeg` extracts their poster frames cleanly.
- **Auto-commit & cleanup**: Newly created notes under `content/gym/YYYY.MM.DD X/` are automatically committed and pushed to `main`. Once all three (`A`, `B`, `C`) exist for a date, it is automatically removed from `~/.config/gym-note/queue.json`.

### Manual / Single-Note Generation

```bash
# Auto-detect the tab with an un-noted logged row
pixi run gym-note

# Specify day letter and/or plan date explicitly
pixi run gym-note C 10.10.2026

# Overwrite an existing note
pixi run gym-note B 10.10.2026 --force
```

