---
name: railway-deploy
description: Use this skill when the user wants to deploy an application that needs a backend, API, server, or database to Railway. Handles Python (FastAPI/Flask), Node.js (Express), and any Dockerfile-based app. Creates a GitHub repo, pushes code, and deploys to Railway automatically.
---

# Railway Deploy Skill

## Overview

This skill deploys full-stack or backend applications to Railway.
Use it when the site needs server-side code, APIs, databases, or any runtime.
For purely static sites (HTML/CSS/JS only), use `github-pages-deploy` instead.

## When to use this skill

- FastAPI / Flask / Django backends
- Express / Node.js APIs
- Apps that need environment variables or secrets
- Apps with database connections (Postgres, Redis)
- Anything that can't be served as static files

## Workflow

### Step 1: Write the application code

Write all app files to `/mnt/user-data/workspace/app-build/`:
- Your main application file (`main.py`, `server.js`, `app.py`, etc.)
- `requirements.txt` or `package.json`
- Any supporting modules

### Step 2: Write a Dockerfile

Always write an explicit `Dockerfile` to `/mnt/user-data/workspace/app-build/Dockerfile`.
The app MUST listen on `$PORT` (Railway injects this):

**Python/FastAPI example:**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
```

**Node.js example:**
```dockerfile
FROM node:20-slim
WORKDIR /app
COPY package*.json .
RUN npm ci --production
COPY . .
CMD node server.js
```

### Step 3: Choose a project name

Pick a short, descriptive name (kebab-case, max 30 chars).
Format: `tc-{topic}` e.g. `tc-weather-api`

### Step 4: Deploy

```bash
python /app/skills/public/railway-deploy/scripts/deploy.py \
  --source-dir /mnt/user-data/workspace/app-build \
  --project-name tc-{name} \
  --description "Brief description of what this app does"
```

The script will:
1. Create a GitHub repo `menonpg/{project-name}`
2. Push your code to it
3. Create a Railway project linked to the GitHub repo
4. Trigger a Railway deployment
5. Return the public Railway URL

### Step 5: Report the result

Tell the user:
- The Railway public URL
- The GitHub repo URL (for future edits)
- Any environment variables they need to set manually in Railway dashboard
- That initial deploy takes ~2–3 minutes to build

## Environment Variables

If the app needs secrets (API keys, DB URLs), tell the user:
"Set these in Railway dashboard → your project → Variables:
- `VARIABLE_NAME`: [description]"

Do NOT hardcode secrets in code or Dockerfile.

## Notes

- Railway free tier: 500 hours/month, $5 credit
- Apps sleep after inactivity on free tier — first request may be slow
- For persistent data, recommend Railway Postgres or Redis add-ons
- Always use `$PORT` not a hardcoded port number
