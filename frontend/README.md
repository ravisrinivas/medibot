# MediBot

RBAC-enforced hybrid RAG chatbot for MediAssist Health Network, built on the
techniques from `advanced__RAG.ipynb` (Docling + HybridChunker, hybrid
dense+BM25 Qdrant retrieval, cross-encoder reranking, SQL RAG over
`mediassist.db`), extended with role-based access control enforced at the
vector store query level.

## Architecture

```
Question + role token
        |
        v
  Analytical question? --(yes, role allowed)--> SQL RAG --> answer
        |
       (no)
        v
  Hybrid retrieval (RBAC-filtered at query time)
        |
        v
  Cross-encoder rerank (top-10 -> top-3)
        |
        v
  LLM answer + citations
```

RBAC is enforced with a single shared Qdrant collection (`medibot_hybrid`).
Every chunk's payload carries `metadata.access_roles`, and every retrieval
query attaches a Qdrant filter matching the caller's role against that
field &mdash; restricted chunks are never fetched from the vector store, so
they can never reach the LLM or leak through a prompt.

## Project layout

```
backend/
  app/
    main.py            FastAPI app: /login, /chat, /collections/{role}, /health
    auth.py             Demo users + in-memory session tokens
    config.py            Models, paths, role -> collection map
    rbac/roles.py        Qdrant filter builder, allowed_collections()
    ingestion/ingest.py  Docling parse + HybridChunker + metadata -> Qdrant (run once)
    rag/hybrid.py         RBAC-filtered hybrid retrieval + reranking + LLM answer
    rag/sql_rag.py        NL -> SQL -> execute -> NL answer over mediassist.db
    rag/router.py         Analytical vs document question routing
  data/mediassist_data/   Assignment source documents + mediassist.db
  requirements.txt
  .env.example
  diagnose.py             Standalone script to inspect Qdrant + test the RBAC filter
frontend/
  pages/login.js          Sign-in page
  pages/chat.js           Sidebar (role, accessible collections) + chat UI
  components/             MessageBubble, SourceChips, RoleBadge
  lib/api.js              Fetch wrapper around the backend
```

## Prerequisites

- **Python 3.10+** with `pip`
- **Node.js LTS** (includes `npm`) &mdash; download from https://nodejs.org
- A free **Groq API key** &mdash; https://console.groq.com/keys

## 1. Backend setup

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Open `.env` and paste in your Groq API key. Confirm `MEDIASSIST_DATA_DIR`
points to `./data/mediassist_data` (already the default) and that your data
folder is actually placed there.

### Run ingestion (once, or whenever source documents change)

```powershell
python -m app.ingestion.ingest
```

This parses all 12 files across `clinical/`, `nursing/`, `billing/`,
`equipment/`, `general/` with Docling's `HybridChunker`, tags every chunk
with the full metadata schema, and builds a local Qdrant index at whatever
path `QDRANT_PATH` points to in `.env` (default `./qdrant_storage`).

Expect ~277 chunks indexed. On Windows, you may see harmless symlink
warnings from `huggingface_hub`/`fastembed` &mdash; safe to ignore, or fixed
by enabling Windows Developer Mode.

### Start the API

```powershell
uvicorn app.main:app --reload
```

Runs on `http://localhost:8000`. Visit `/docs` for the interactive schema
(note: testing auth-protected endpoints through Swagger UI can be finicky
&mdash; see Troubleshooting below. PowerShell is more reliable for manual
testing.)

## 2. Frontend setup

```powershell
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

Open `http://localhost:3000` &mdash; it redirects to `/login`. The backend
must already be running (CORS is configured to allow `localhost:3000`
specifically).

### Demo users

| Username      | Password    | Role               |
|---------------|-------------|--------------------|
| dr_patel      | doctor123   | doctor             |
| nurse_lee     | nurse123    | nurse              |
| billing_kim   | billing123  | billing_executive  |
| tech_ortiz    | tech123     | technician         |
| admin         | admin123    | admin              |

## 3. Validating RBAC works

1. Log in as `dr_patel`, ask a clinical question (e.g. drug dosage) &mdash;
   should succeed with sources from `clinical`/`nursing`/`general`.
2. Log in as `tech_ortiz`, ask the **same** clinical question &mdash; should
   refuse, with sources (if any) only from `equipment`/`general`.
3. Log in as `billing_kim` or `admin`, ask an analytical question (e.g.
   "How many claims are escalated versus resolved?") &mdash; should return
   `retrieval_type: "sql"` with real numbers.
4. Log in as `nurse_lee` or `tech_ortiz`, ask the same analytical question
   &mdash; should return `retrieval_type: "blocked"`.

`backend/diagnose.py` can also inspect the Qdrant collection directly and
test the RBAC filter without going through the API (stop `uvicorn` first,
since local Qdrant only allows one process at a time).

## Status

- [x] Ingestion pipeline (Docling + HybridChunker, full metadata schema)
- [x] RBAC-filtered hybrid retrieval + cross-encoder reranking
- [x] SQL RAG over `mediassist.db`, gated to billing_executive/admin
- [x] FastAPI backend (`/login`, `/chat`, `/collections/{role}`, `/health`)
- [x] Next.js frontend (login, chat UI, source citations, RBAC refusal styling)
- [ ] Adversarial-prompt test suite write-up (see validation steps above as a starting point)
