# ProofLens AI — Technical Architecture & Engineering Documentation

**Platform:** ProofLens AI  
**Version:** 0.3.0  
**Baseline Tech Stack:** FastAPI (Python 3.13/3.14) + Next.js 16 (React 19, TypeScript) + Supabase PostgreSQL with `pgvector` + Supabase Storage  
**Governing Rules:** `AGENTS.md` (Strict Multi-Tenant Isolation, Zero Secret Leakage, Grounded Evidence Only)

---

## 1. System Architecture Overview

ProofLens AI is an evidence-first document intelligence platform built as a high-performance modular monolith designed for scalable cloud deployment:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Next.js 16 Frontend UI                          │
│     (App Router, TypeScript, TailwindCSS, Lucide-React, Glassmorphism)  │
│  - Document Workspace  - Grounded Q&A  - 4-Tier Claim Verifier        │
│  - Multi-Turn Threads  - Provenance Viewer - Investigation Audit Trail │
│  - Hosted on Vercel (Root Directory: frontend)                        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ REST / JSON (JWT Bearer Auth)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        FastAPI 0.115 Backend                           │
│  (Deployed on Render Web Service, ASGI Uvicorn listening on $PORT)     │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Security & Auth: JWT, Bcrypt, Tenant Workspace Isolation Dep    │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │ Multi-Turn Chat: Persistent Thread-Based Conversations Engine    │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │ Ingestion & Chunking: PyMuPDF, Sliding Window (600 / 100 overlap)│  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │ Unified Storage: Supabase Storage (Cloud) / Local Disk (Dev)     │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │ Embedding Engine: Gemini Embedding 2 (768-dim) + Fallback Vec    │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │ Retrieval Layer: pgvector Cosine Distance (<=>), Top-K Filtering │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │ Grounded Synthesis: Gemini 3.5 Flash / 3.5 Flash-Lite + Fallback │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │ Citation Validator: Hallucination Rejection, Provenance Anchor  │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │ Claim Verifier & Comparator: 4-Tier Verification, Doc Diff Matrix│  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │ History & Reporting: Chronological Timeline, Markdown Exporter   │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │ Health & Probes: /health and / endpoints for Load Balancer Probes│  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───────┬───────────────────────────┬────────────────────────────┬───────┘
        │                           │                            │
        ▼                           ▼                            ▼
┌─────────────────────────┐  ┌───────────────────────┐  ┌───────────────────────┐
│ Supabase PostgreSQL DB  │  │ Google Gemini AI API  │  │ Supabase Storage      │
│ - pgvector (768-dim)    │  │ - gemini-3.5-flash    │  │ - Persistent PDF Docs │
│ - Session/Tx Pooler     │  │ - gemini-embedding-2  │  │ - Private Bucket      │
│ - Alembic Migrations    │  │ - gemini-3.5-fl-lite  │  │ - Authenticated REST  │
└─────────────────────────┘  └───────────────────────┘  └───────────────────────┘
```

---

## 2. Database Schema & Data Isolation

All tables are defined in SQLAlchemy 2.0 async declarative models. Tenant ownership is enforced at the query level in data access functions—never relying on client-supplied identifiers alone.

### Core Tables
1. **`users`**: User identity, bcrypt-hashed credentials, full name, timestamps.
2. **`workspaces`**: Tenant container owned by a primary user.
3. **`workspace_members`**: RBAC membership mapping users to workspaces (`owner`, `admin`, `member`, `viewer`).
4. **`documents`**: Document metadata, filename, MIME type, file size, SHA-256 hash, page count, storage path (`local://` or `supabase://`), status (`uploaded`, `processing`, `indexed`, `error`).
5. **`document_pages`**: Page-level extracted text and dimensions for PDF navigation.
6. **`document_chunks`**: Individual sliding-window text segments with foreign keys to `document_id` and `workspace_id`.
   - `embedding`: Column of type `vector(768)` indexed via pgvector.
7. **`conversations`**: Persistent multi-turn conversation threads per workspace and user.
8. **`chat_messages`**: Ordered messages inside a conversation thread (`role`, `content`, `status`, `citations_json`).
9. **`query_runs`**: Record of Q&A queries submitted by users per workspace.
10. **`answers`**: Synthesized answer text, status (`supported`, `partially_supported`, `insufficient_evidence`), confidence score.
11. **`citations`**: Validated chunk provenance references linked to answers.
12. **`claim_verifications`**: 4-tier claim verification records (`status`, `confidence_score`, `explanation`).
13. **`claim_citations`**: Grounding evidence passages linked to claims.

### Multi-Tenant Workspace Isolation
Every API endpoint accesses data through the `CurrentWorkspaceDep` dependency:
```python
async def get_current_workspace(
    workspace_id: str,
    current_user: CurrentUserDep,
    db: DBDep,
) -> Workspace:
    # Verifies that current_user has an active membership record in workspace_id
    # Raises 403 Forbidden if not authorized.
```
All retrieval, documents, chunks, conversations, and audit trail queries strictly append `WHERE workspace_id = :workspace_id`. Cross-tenant data leakage is structurally impossible.

---

## 3. Persistent PDF Storage Architecture

Render's container filesystem is ephemeral; files written to `./storage/` are discarded whenever the service restarts, scales, or redeploys. To guarantee persistence without exposing private documents:

### Unified Storage Coordinator (`backend/app/services/storage/`)
- Abstract interface: `StorageProvider` defining `save()`, `get()`, and `delete()`.
- **Local Provider (`LocalStorageProvider`):** Writes to `./storage/docs/` with URI format `local://<rel_path>`. Used in local development and offline automated tests.
- **Supabase Storage Provider (`SupabaseStorageProvider`):**
  - Uploads PDF files to the private bucket `prooflens-documents` via Supabase Storage REST API (`/storage/v1/object/...`).
  - Authenticates securely server-side using `SUPABASE_SERVICE_ROLE_KEY`.
  - Storage URI format: `supabase://<bucket>/<rel_path>`.
  - Document retrieval (`GET /documents/{id}/file`) transparently streams file bytes from Supabase Storage without making the bucket public.

---

## 4. Database Migrations & Engine Resilience

### Async Database URL Normalization (`database.py`)
Supabase connection strings provided via dashboard typically use `postgresql://` or `postgres://`. In SQLAlchemy 2.0+, `create_async_engine()` maps `postgresql://` to `psycopg` instead of `asyncpg`.
The `normalize_async_database_url()` utility automatically:
1. Normalizes `postgresql://` and `postgres://` to `postgresql+asyncpg://`.
2. Translates `sslmode=require` into `ssl=require` (which `asyncpg` natively recognizes).

### Supabase Connection Pooling
Supabase serverless connection poolers (port 6543) close idle TCP sockets after a brief inactivity period. The SQLAlchemy engine is hardened with:
- `pool_pre_ping=True`: Tests connection health before emitting queries.
- `pool_recycle=300`: Automatically recycles connections older than 5 minutes to prevent stale sockets.
- `pool_size=10`, `max_overflow=20`: Handles concurrent request bursts.

### Alembic Migration Pipeline
- Configuration: `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako`.
- Initial Schema (`alembic/versions/0001_initial_schema.py`):
  - Emits `CREATE EXTENSION IF NOT EXISTS vector;` on PostgreSQL targets.
  - Creates all 13 tables, indexes, and cascading foreign keys.
- Production Startup Safety: In `main.py`, automatic table creation via `Base.metadata.create_all` is bypassed when `APP_ENV=production`. Render runs `alembic upgrade head` during release.

---

## 5. RAG Pipeline Implementation

### Step 1: Ingestion & Extraction
- Handled in `backend/app/services/document/document_service.py`.
- Format validation: Allowed MIME types (`application/pdf`, `text/plain`, `text/markdown`), size limit checked via `settings.MAX_FILE_SIZE_MB` (default 15MB).
- Page-aware parsing with PyMuPDF (`fitz`), preserving exact page numbering for every extracted text segment.

### Step 2: Sliding-Window Chunking
- Handled in `backend/app/services/chunking/text_chunker.py`.
- Target chunk size: 600 tokens (`settings.CHUNK_SIZE_TOKENS`).
- Overlap size: 100 tokens (`settings.CHUNK_OVERLAP_TOKENS`).
- Maintains page boundaries and chunk indices so that citations point to exact pages.

### Step 3: Embedding Generation
- Handled in `backend/app/services/embedding/embedding_service.py`.
- Candidate model: `gemini-embedding-2` producing 768-dimensional normalized vectors.
- Includes a deterministic semantic embedding fallback for test and offline environments so that tests run reliably without network dependencies.

### Step 4: Vector Retrieval
- Handled in `backend/app/services/retrieval/retrieval_service.py`.
- SQL Query uses pgvector cosine distance operator (`<=>`):
  ```sql
  SELECT document_chunks.id, document_chunks.content, documents.filename,
         1.0 - (document_chunks.embedding <=> :query_vec) AS similarity
  FROM document_chunks
  JOIN documents ON document_chunks.document_id = documents.id
  WHERE document_chunks.workspace_id = :workspace_id
  ORDER BY (document_chunks.embedding <=> :query_vec) ASC
  LIMIT :top_k;
  ```
- Chunks below `settings.SIMILARITY_THRESHOLD` (0.35) or outside the workspace are rejected.

### Step 5: Grounded Answer Synthesis
- Handled in `backend/app/services/generation/gemini_generator.py`.
- Structured system instructions require answers strictly grounded in delimited `<evidence_context>` passages.
- Models attempted in order:
  1. `gemini-3.5-flash`
  2. `gemini-3.5-flash-lite`
- Enforces JSON output schema: `answer`, `status`, `confidence_score`, `citations`.
- **Offline / Demand Spike Fallback Engine:**
  - Evaluates query intent.
  - Supports identity queries (e.g., "whose resume is this?", "who is the applicant?") by parsing Page 1 headers for verified candidate names while blacklisting non-name business document titles.
  - Substantive content word filtering with comprehensive English stop words; requires $\ge 35\%$ content word match to prevent false positives on prepositions.
  - When evidence is lacking, outputs clean `insufficient_evidence` with empty citations.

### Step 6: Citation Validation & Anti-Hallucination
- Handled in `backend/app/services/citation/citation_validator.py`.
- Cross-references raw citations from the LLM against the actual retrieved chunks.
- Validates that `chunk_id`, `document_id`, and `page_number` match real database records.
- Verifies that quoted excerpts exist within the candidate chunk content.
- **Strict Invariant:** If `raw_citations` is empty (e.g., answer abstained), the validator returns `[]` (empty list), guaranteeing that the UI never displays contradictory source citations when an answer is abstained.

---

## 6. Multi-Turn Persistent Conversations Engine

- Implemented in `backend/app/api/v1/conversations.py` and `backend/app/services/qa/qa_service.py`.
- First user question in a new session creates a `Conversation` record with title auto-derived from the question.
- Subsequent follow-ups pass `conversation_id`, which appends new user and assistant `ChatMessage` records to the active thread.
- Context-aware synthesis injects previous conversation history into the Gemini prompt while grounding responses in current retrieved document chunks.
- Frontend sidebar dynamically loads past threads with active selection highlighting and deletion.

---

## 7. Known Gotchas & Resolved Edge Cases

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **`psycopg` Missing Error** | SQLAlchemy 2.0 defaults to `psycopg` when URL has `postgresql://`. | `normalize_async_database_url()` in `database.py` rewrites to `postgresql+asyncpg://`. |
| **`CORS_ORIGINS` Crash on Render** | `pydantic-settings` executes `json.loads()` on `List[str]` env vars, failing on comma-separated strings (`JSONDecodeError: char 0`). | Typed as `Union[List[str], str]` with `env_ignore_empty=True` and post-validator in `config.py`. |
| **Render Health Check 404** | Render probes `/health`, but endpoint was nested under `/api/v1/health`. | Added root-level `@app.get("/health")` and `@app.get("/")` returning `200 OK` in `main.py`. |
| **Vercel Build Missing `api.ts`** | Root `.gitignore` had bare `lib/` rule, which accidentally ignored `frontend/src/lib/`. | Scoped Python rules to `/lib/` and `/lib64/` and explicitly added `!frontend/src/lib/`. |
| **Vercel API URL Format Mismatch** | Deployments without trailing `/api/v1` threw 404 on API calls. | In `frontend/src/lib/api.ts`, `API_BASE_URL` auto-appends `/api/v1` if missing. |
| **Model 404 Error** | `gemini-2.5-flash` deprecated on Google AI Studio for new keys. | Migrated to `gemini-3.5-flash` with graceful fallback to `gemini-3.5-flash-lite`. |
| **HttpOptions Timeout** | `google.genai.types.HttpOptions.timeout` expects milliseconds, not seconds. | Configured timeout as `15000` (15,000 ms = 15s). |
| **Contradictory Citations** | Citation validator derived fallback chunks when answer abstained. | Enforced `return []` whenever answer status is `insufficient_evidence`. |
| **History Datetime TypeError** | Mixed naive and UTC-aware datetimes when merging history items. | Applied `_to_utc()` normalizer before sorting. |
