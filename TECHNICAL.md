# ProofLens AI — Technical Architecture & Engineering Documentation

**Platform:** ProofLens AI  
**Version:** 0.2.0  
**Baseline Tech Stack:** FastAPI (Python 3.13) + Next.js 16 (React 19, TypeScript) + PostgreSQL 18 with `pgvector 0.8.7`  
**Governing Rules:** `AGENTS.md` (Strict Multi-Tenant Isolation, Zero Secret Leakage, Grounded Evidence Only)

---

## 1. System Architecture Overview

ProofLens AI is an evidence-first document intelligence platform built as a high-performance modular monolith.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Next.js 16 Frontend UI                          │
│     (App Router, TypeScript, TailwindCSS, Lucide-React, Glassmorphism)  │
│  - Document Workspace  - Grounded Q&A  - 4-Tier Claim Verifier        │
│  - Provenance Viewer   - Investigation Audit Trail  - Report Exporter  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ REST / JSON (JWT Bearer Auth)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        FastAPI 0.115 Backend                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Security & Auth: JWT, Bcrypt, Tenant Workspace Isolation Dep    │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │ Ingestion & Chunking: PyMuPDF, Sliding Window (600 / 100 overlap)│  │
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
│  └──────────────────────────────────────────────────────────────────┘  │
└──────────────────┬─────────────────────────────────┬───────────────────┘
                   │                                 │
                   ▼                                 ▼
┌─────────────────────────────────────┐   ┌──────────────────────────────┐
│       PostgreSQL 18 + pgvector      │   │     Google Gemini API        │
│  - users, workspaces, members       │   │  - gemini-3.5-flash (QA)     │
│  - documents, pages, chunks (768d)  │   │  - gemini-embedding-2 (Vec)  │
│  - query_runs, answers, citations   │   │  - gemini-3.5-flash-lite     │
│  - claim_verifications, citations   │   │                               │
└─────────────────────────────────────┘   └──────────────────────────────┘
```

---

## 2. Database Schema & Data Isolation

All tables are defined in SQLAlchemy 2.0 async declarative models. Tenant ownership is enforced at the query level in data access functions—never relying on client-supplied identifiers alone.

### Core Tables
1. **`users`**: User identity, hashed credentials, full name, timestamps.
2. **`workspaces`**: Tenant container owned by a primary user.
3. **`workspace_members`**: RBAC membership mapping users to workspaces (`owner`, `admin`, `member`, `viewer`).
4. **`documents`**: Document metadata, filename, MIME type, file size, SHA-256 hash, page count, storage path, status (`uploaded`, `processing`, `indexed`, `error`).
5. **`document_pages`**: Page-level extracted text and dimensions for PDF navigation.
6. **`document_chunks`**: Individual sliding-window text segments with foreign keys to `document_id` and `workspace_id`.
   - `embedding`: Column of type `vector(768)` indexed via pgvector.
7. **`query_runs`**: Record of Q&A queries submitted by users per workspace.
8. **`answers`**: Synthesized answer text, status (`supported`, `partially_supported`, `insufficient_evidence`), confidence score.
9. **`citations`**: Validated chunk provenance references linked to answers.
10. **`claim_verifications`**: 4-tier claim verification records (`status`, `confidence_score`, `explanation`).
11. **`claim_citations`**: Grounding evidence passages linked to claims.

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
All retrieval, documents, chunks, and audit trail queries strictly append `WHERE workspace_id = :workspace_id`. Cross-tenant data leakage is structurally impossible.

---

## 3. RAG Pipeline Implementation

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
  1. Configured model (if not deprecated 2.5).
  2. `gemini-3.5-flash`
  3. `gemini-3.5-flash-lite`
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

## 4. 4-Tier Claim Verification Engine

Handled in `backend/app/services/claims/claim_verifier.py`:
- Evaluates individual claims against document evidence.
- Status classification:
  - **Supported**: Direct factual evidence proves the claim.
  - **Partially Supported**: Core claim has partial evidence, but specific qualifications or dates are missing.
  - **Contradicted**: Document evidence directly contradicts the statement.
  - **Insufficient Evidence**: The available documents contain no evidence to verify or refute the claim.
- Cross-document comparison matrix in `backend/app/services/comparison/doc_comparator.py` maps common and conflicting statements across multiple uploaded files.

---

## 5. Investigation History & Audit Reports

- History endpoint: `/api/v1/workspaces/{workspace_id}/history`
  - Merges Q&A query runs and claim verifications into a chronological timeline.
  - Normalizes timestamps to UTC to ensure clean cross-database sorting.
- Report export endpoint: `/api/v1/workspaces/{workspace_id}/reports/export`
  - Generates comprehensive Markdown audit reports with telemetry, document inventory, evidence Q&A logs, and 4-tier verification results.
  - Supports direct browser download attachment via `?download=true`.

---

## 6. Security, Configuration & Production Hygiene

- **Zero Secret Exposure:** Configuration is managed through `backend/app/core/config.py` using `pydantic-settings`.
- **Environment Separation:** `.env` is never checked into Git or exposed to the client. Frontend only receives public configuration; all AI calls and database transactions are server-side.
- **Prompt Injection Defense:** Document text inside `<evidence_context>` is strictly treated as untrusted passive data. System prompts instruct the LLM never to obey instructions found within document passages.

---

## 7. Known Gotchas & Resolved Edge Cases

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **Windows pgvector 0.8.7** | PostgreSQL 18 Windows installer has no native pgvector bundle. | Compiled `vector.dll` via MSVC against PG 18 include headers and installed to `PostgreSQL\18\lib`. |
| **Model 404 Error** | `gemini-2.5-flash` deprecated on Google AI Studio for new keys. | Migrated to `gemini-3.5-flash` with graceful fallback to `gemini-3.5-flash-lite`. |
| **HttpOptions Timeout** | `google.genai.types.HttpOptions.timeout` expects milliseconds, not seconds. | Configured timeout as `15000` (15,000 ms = 15s). |
| **Contradictory Citations** | Citation validator derived fallback chunks when answer abstained. | Enforced `return []` whenever answer status is `insufficient_evidence`. |
| **History Datetime TypeError** | Mixed naive and UTC-aware datetimes when merging history items. | Applied `_to_utc()` normalizer before sorting. |
