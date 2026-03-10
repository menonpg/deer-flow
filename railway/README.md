# Deploying DeerFlow on Railway

Run DeerFlow on Railway in ~10 minutes with free AI inference via MiniMax cloud + optional Ollama.

## Quick Start

### 1. Fork this repo & connect to Railway

1. Fork `bytedance/deer-flow` to your GitHub account
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub repo
3. Select your fork

### 2. Add a Persistent Volume (required)

In Railway dashboard → backend service → **Volumes** → Add Volume:
- Mount path: `/data`
- Recommended size: 5GB

This stores LangGraph thread checkpoints, agent memory, and the SQLite database.
Without it, all state resets on every deploy.

### 3. Set Environment Variables (backend service)

**Required:**
| Variable | Where to get it |
|---|---|
| `MINIMAX_API_KEY` | [minimaxi.com/en](https://www.minimaxi.com/en/) — free tier available |
| `DEER_FLOW_CONFIG_PATH` | Set to `/app/config.yaml` |

**Optional:**
| Variable | Notes |
|---|---|
| `TAVILY_API_KEY` | [tavily.com](https://tavily.com) — 1,000 free searches/month |
| `OLLAMA_URL` | Set after adding Ollama service (see below) |

### 4. Set Environment Variables (frontend service)

Once the backend service is deployed, copy its public URL and set:
| Variable | Value |
|---|---|
| `NEXT_PUBLIC_BACKEND_BASE_URL` | `https://<your-backend-service>.railway.app` |
| `NEXT_PUBLIC_LANGGRAPH_BASE_URL` | `https://<your-backend-service>.railway.app/api/langgraph` |
| `BETTER_AUTH_SECRET` | Any random string (32+ chars) |

### 5. Deploy

Trigger a deploy on both services. The backend takes ~3 minutes to build.

Open the frontend service URL — DeerFlow should be running.

---

## Adding Ollama (Free Local Inference)

1. In your Railway project → **New Service** → search "Ollama" in the marketplace
2. Add the Ollama service and note its public domain
3. Set in the **backend** service:
   ```
   OLLAMA_URL = https://<ollama-service>.railway.app
   ```
4. Pull a model (run in Railway shell for the Ollama service):
   ```bash
   ollama pull llama3.2      # 2GB, good for general tasks
   ollama pull deepseek-r1   # For reasoning tasks
   ```
5. Ollama will now appear as a model option in the DeerFlow UI alongside MiniMax

**Railway memory requirements for Ollama:**
| Model | Min RAM |
|---|---|
| llama3.2 (3B) | 4GB |
| llama3.1 (8B) | 8GB |
| deepseek-r1 (7B) | 8GB |
| mistral (7B) | 8GB |

---

## Cost on Railway

| Service | Est. Monthly (idle) | Est. Monthly (active) |
|---|---|---|
| Backend (512MB RAM) | ~$5 | ~$10–15 |
| Frontend (256MB RAM) | ~$3 | ~$5 |
| Ollama (8GB RAM) | ~$20 | ~$25–35 |
| **Total (no Ollama)** | **~$8/mo** | **~$15–20/mo** |
| **Total (with Ollama)** | **~$28/mo** | **~$40–55/mo** |

**AI inference costs:** $0 with MiniMax free tier or Ollama. If you hit MiniMax's free limits,
MiniMax API pricing is very competitive — roughly $0.15/million input tokens for Text-01.

---

## Architecture

```
Railway Project
├── backend service (Dockerfile.railway-backend)
│   ├── Gateway API      :8001  — config, memory, models API
│   ├── LangGraph Server :2024  — agent execution engine
│   └── /data volume           — checkpoints + memory (persistent)
│
├── frontend service (Dockerfile.railway-frontend)
│   └── Next.js          :3000  — web UI
│
└── ollama service (optional, Railway marketplace)
    └── Ollama           :11434 — local model inference
```

## Troubleshooting

**"Cannot connect to LangGraph"** — check that `NEXT_PUBLIC_LANGGRAPH_BASE_URL` points to the backend service URL, not the frontend.

**State resets on every deploy** — make sure the `/data` volume is attached to the backend service.

**Ollama model not loading** — the Ollama service needs enough RAM. Use Railway's scale controls to give it 8GB+ for 7B models.

**MiniMax 401 error** — double-check `MINIMAX_API_KEY` is set on the backend service (not frontend).
