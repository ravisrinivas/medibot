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
Every chunk's payload carries `access_roles`, and every retrieval query
attaches a Qdrant filter matching the caller's role against that field --
restricted chunks are never fetched from the vector store, so they can
never reach the LLM or leak through a prompt.

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
frontend/                 (to be built: Next.js chat UI)
```

## Setup (VS Code, Windows/macOS/Linux)

1. Open this folder in VS Code.
2. Open a terminal in `backend/` and create a virtual environment:
   ```
   cd backend
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   source .venv/bin/activate     # macOS/Linux
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and paste in your Groq API key
   (get one free at https://console.groq.com/keys):
   ```
   copy .env.example .env   # Windows
   cp .env.example .env     # macOS/Linux
   ```
4. Run the ingestion pipeline once to build the Qdrant index:
   ```
   python -m app.ingestion.ingest
   ```
   This parses every PDF/Markdown file under `data/mediassist_data/`,
   chunks it with Docling's `HybridChunker`, tags each chunk with the full
   metadata schema (`source_document`, `collection`, `access_roles`,
   `section_title`, `chunk_type`), and indexes it into a local Qdrant store
   at `qdrant_storage/`.
5. Start the API server:
   ```
   uvicorn app.main:app --reload
   ```
6. Visit http://localhost:8000/docs to try the endpoints interactively.

### Demo users

| Username      | Password    | Role               |
|---------------|-------------|--------------------|
| dr_patel      | doctor123   | doctor             |
| nurse_lee     | nurse123    | nurse              |
| billing_kim   | billing123  | billing_executive  |
| tech_ortiz    | tech123     | technician         |
| admin         | admin123    | admin              |

### Try it

```
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "dr_patel", "password": "doctor123"}'

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token from login>" \
  -d '{"question": "What is the standard dose for Amoxicillin?"}'
```

## Pushing to GitHub

From the project root (this folder, containing `backend/` and `frontend/`):

```
git init
git add .
git commit -m "Initial MediBot backend: RBAC-enforced hybrid RAG + SQL RAG"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

`.env` and the `qdrant_storage/` index are gitignored, so they won't be
pushed -- anyone cloning the repo needs to add their own `.env` and re-run
the ingestion step.

## Status / next steps

- [x] Ingestion pipeline (Docling + HybridChunker, full metadata schema)
- [x] RBAC-filtered hybrid retrieval + cross-encoder reranking
- [x] SQL RAG over `mediassist.db`, gated to billing_executive/admin
- [x] FastAPI backend (`/login`, `/chat`, `/collections/{role}`, `/health`)
- [ ] Next.js frontend (login, chat UI, source citations, RBAC refusal messages)
- [ ] Adversarial-prompt test suite + write-up for the README
