# Happy Valley Field Guide

A Markdown-first local acclimation guide for the Lenoir region, organized by nearest town. Each event or place gets one Markdown file in the folder for its nearest town/community. Generated HTML views will organize the same files by tags, dates, towns, and seasons.

## Content convention

```text
content/
  lenoir/
    sculpture-celebration.md
  happy-valley/
    fort-defiance.md
  blowing-rock/
    art-in-the-park.md
```

The town folder is the physical filing location. Tags are the classification system.

## Entry frontmatter

```yaml
---
title:
type: event # event | place
town:
county:
address:
date_start:
date_end:
time:
season:
tags: []
cost:
dog_friendly:
description_short:
source_urls: []
status: needs-confirmation
---
```

Use `status: confirmed` only when the date/details come from an official or local source for the relevant year.

## Generate and publish

Generate the site with:

```powershell
python .\scripts\generate-html.py
```

The Markdown files under `content\`, the taxonomy files under `taxonomy\`, and the generator under `scripts\` are the source-controlled editing surface. The generator writes both `site\index.html` for local preview and root `index.html` for GitHub Pages.

GitHub Pages publishes root `index.html` from the `main` branch. A GitHub Actions workflow rebuilds and commits the generated HTML whenever source content changes on GitHub, so editing Markdown in the repo updates the public site after the workflow finishes.

The map uses MapLibre GL plus OpenFreeMap vector tiles, so it needs to run from a real web host such as GitHub Pages, Azure Static Web Apps, or another static hosting endpoint.
