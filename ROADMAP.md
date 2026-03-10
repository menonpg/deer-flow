# Roadmap — Create AI Everywhere

## In Progress
- ✅ Railway deployment (backend + frontend)
- ✅ Multi-model support (Azure GPT-5, GPT-4o, Gemini, Ollama)
- ✅ Frontend ↔ backend proxy wiring

## Planned

### 🧠 Agent Soul (high priority)
Give the agent a persistent persona and context within each chat — like a SOUL.md injected into the system prompt. Currently the agent starts cold every conversation with no identity or user context.

**What this means:**
- Custom system prompt per deployment (who the agent is, what it knows about the user/stack)
- Possibly load a `soul.md` or `agent-context.md` from the `/data` volume at startup
- Lightweight persistent facts that carry across sessions (name, project context, preferences)
- Make it feel like "your AI" not a generic task runner

**Approach:**
- Add a `soul_path` config option in `config.yaml` pointing to a markdown file
- Inject its content into the `apply_prompt_template()` call in `lead_agent/agent.py`
- Expose a settings UI field to edit the soul/persona from the frontend

### 🎨 Rebrand to "Create AI Everywhere"
- ✅ Rename all UI strings from "DeerFlow" → "Create AI Everywhere" / "CreateAI"
- ✅ Update landing page hero, header, footer
- Update favicon/logo to match new brand
- Custom domain / landing page

### 🔧 Other
- Ollama volume persistence (so model manifests survive restarts)
- LangGraph production mode (replace `langgraph dev` with a production server)
- Auth (BetterAuth GitHub login)
