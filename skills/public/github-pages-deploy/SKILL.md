---
name: github-pages-deploy
description: Use this skill when the user wants to deploy, publish, host, or share a static website (HTML/CSS/JS). Deploys to GitHub Pages and returns a live public URL at sites.thinkcreateai.com. Use for: landing pages, reports as webpages, portfolios, dashboards, documentation sites, any static frontend.
---

# GitHub Pages Deploy Skill

## Overview

This skill deploys static websites to GitHub Pages under `sites.thinkcreateai.com/{slug}`.
Use it for any site that is purely HTML/CSS/JS — no server-side code needed.
For sites that need a backend API, use the `railway-deploy` skill instead.

## Workflow

### Step 1: Build the site files

Write all site files to `/mnt/user-data/workspace/site-build/`:
- `index.html` — main entry point (required)
- `style.css`, `script.js`, etc. — any supporting assets
- Subdirectories are supported

The site must be fully self-contained (no external build step).
Inline critical CSS/JS if possible to minimize file count.

**ALWAYS include the ThinkCreate.AI favicon in every `index.html`** — add this inside `<head>`:
```html
<link rel="icon" type="image/svg+xml" href="https://ask.themenonlab.com/favicon.svg">
<link rel="shortcut icon" href="https://ask.themenonlab.com/favicon.svg">
```

### Step 2: Choose a slug

Create a short, descriptive slug for the site (kebab-case, max 40 chars).
Format: `{topic}-{YYYYMMDD}` e.g. `startup-landing-20260310`

### Step 3: Deploy

```bash
python /app/skills/public/github-pages-deploy/scripts/deploy.py \
  --source-dir /mnt/user-data/workspace/site-build \
  --slug {your-slug} \
  --title "Human-readable site title"
```

The script will:
1. Clone the `menonpg/thinkcreateai-sites` repo
2. Copy your files to `sites/{slug}/`
3. Commit and push
4. Return the live URL

### Step 4: Report the result

After the script prints the URL, tell the user:
- The live URL: `https://sites.thinkcreateai.com/sites/{slug}/`
- What the site contains
- That it may take 1–2 minutes to propagate on first deploy

## Example

User: "Create a landing page for my SaaS product"

1. Write `index.html` (full page with hero, features, CTA)
2. Write `style.css` if needed
3. Run deploy script with slug `saas-landing-20260310`
4. Return: "Your site is live at https://sites.thinkcreateai.com/sites/saas-landing-20260310/"

## Notes

- GitHub Pages caches aggressively — updates may take 1–3 minutes to show
- Max file size: 100MB per file, 1GB total repo
- No server-side code (PHP, Python, Node) — static only
- HTTPS is automatic via GitHub Pages + Cloudflare
