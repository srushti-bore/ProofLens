# ProofLens AI — Debug Incorrect Evidence Abstention and Answer Generation

## Context

I tested the current ProofLens AI application locally at `localhost:3000`.

User question:
"whose resume is this?"

The application returned:
"Explicit Abstention: Evidence is insufficient or out-of-scope."

It also displayed these source references:
- `Sayali_Ingole_FrontEnd_Intern_Resume.pdf` (p.1)
- `Sayali_Ingole_FrontEnd_Intern_Resume.pdf` (p.2)

The UI shows verified source references, but the answer does not explain whether the resume owner can be identified from the actual document evidence.

This is a potential RAG retrieval, evidence-selection, or answer-generation issue. Do not assume the root cause before investigating.

## Objective

Audit and debug the complete existing ProofLens AI question-answering pipeline to determine why a question about document identity returns an insufficient-evidence response.

The application must answer questions accurately when supporting evidence exists in the uploaded document. It must abstain when the evidence genuinely does not support an answer.

## 1. Trace the Actual Pipeline

Inspect the existing implementation and trace the real execution path for a user question:

1. User question submission from the frontend.
2. API request and backend route.
3. Query preprocessing and embedding generation.
4. Vector retrieval and any keyword/hybrid retrieval.
5. Retrieved chunks, document IDs, page metadata, and similarity/ranking information.
6. Reranking, filtering, thresholds, and context construction, if implemented.
7. LLM prompt construction and answer generation.
8. Evidence validation, citation validation, and abstention logic.
9. Final API response and frontend rendering.

Identify the exact stage where relevant evidence may be lost or incorrectly rejected.

Do not guess the cause or change thresholds blindly.

## 2. Inspect the Actual Uploaded PDF Evidence

Use the existing document records and available source-inspection functionality to verify whether the resume's actual contents identify its owner.

Check:
- Extracted text from the first pages.
- Whether the person's name appears in the extracted text.
- Page-level metadata and chunk boundaries.
- Whether the relevant name is stored and searchable.
- Whether retrieval returns the chunk containing the name.
- Whether the answer-generation context includes that chunk.
- Whether the final answer validator incorrectly rejects an evidence-supported answer.

The filename alone must not be treated as sufficient proof of the person's identity.

If the document explicitly identifies its owner and the evidence is available, the application should answer using that evidence and cite the correct source/page. If the name cannot be established from the actual document, abstention is correct.

## 3. Audit Retrieval and Evidence Selection

Check the existing implementation for:

- Chunking that separates names from relevant resume content.
- Page-aware extraction and page-number preservation.
- Incorrect document or workspace filtering.
- Similarity thresholds that exclude relevant chunks.
- Retrieval top-k limits and ranking issues.
- Metadata mismatches between stored chunks and citations.
- Context truncation or relevant evidence being dropped.
- Overly strict evidence validation or abstention rules.
- Query preprocessing that changes the user's intended question.
- Embedding model/configuration inconsistencies, if present.

Use actual logs, existing tests, database records, and source code as evidence for the diagnosis. Do not expose secrets or sensitive document contents unnecessarily.

## 4. Fix the Root Cause

After identifying the cause, implement the smallest correct fix.

Requirements:
- Reuse the existing architecture and configured model/provider.
- Keep retrieval and generation configurable; do not hardcode thresholds, model IDs, API keys, or environment-specific values.
- Preserve document ownership, workspace isolation, and authorization checks.
- Preserve page-level citations and source attribution.
- Never fabricate a person's name, page number, quotation, or citation.
- Do not remove abstention merely to make answers appear more helpful.
- Do not replace real retrieval or LLM calls with mock responses.
- Do not redesign the frontend for a backend evidence-quality issue.

## 5. Add Regression Tests

Add or update tests for these cases:

**Case A — Answerable identity question**
The document explicitly contains a person's name, and retrieval returns the supporting passage. The answer should identify the person and cite the correct document/page.

**Case B — Filename-only evidence**
The filename contains a person's name, but the actual document contents do not establish the owner's identity. The system must not treat the filename alone as verified evidence.

**Case C — Genuinely insufficient evidence**
The relevant information is absent from the available document contents. The system should abstain and explain the limitation.

**Case D — Retrieval failure**
The document contains the answer, but the relevant passage is not retrieved. The system should expose or handle the retrieval failure appropriately rather than incorrectly treating it as proof that the information is absent.

**Case E — Citation correctness**
Every cited source and page must correspond to actual retrieved evidence.

**Case F — Workspace isolation**
A question must never retrieve documents or evidence belonging to another user or workspace.

Use the existing test framework and fixtures where possible. Do not fabricate passing test results.

## 6. Security and Project Constraints

- Read `AGENTS.md` if present.
- Inspect the current code before editing.
- Preserve completed backend work and existing frontend UI/UX.
- Do not rebuild the application from scratch.
- Never access, read, print, modify, or expose `.env` files or secret values.
- Do not hardcode credentials.
- Do not make unrelated schema, authentication, deployment, or infrastructure changes.
- Do not commit or push changes without explicit approval.

## 7. Final Report

Report:
1. Root cause, supported by actual code paths or test evidence.
2. Whether the failure occurred in extraction, retrieval, ranking, context construction, generation, validation, or frontend rendering.
3. Exact files changed and the reason for each change.
4. Actual regression tests added and their results.
5. Whether the original question now produces an evidence-supported answer.
6. Any remaining limitations.
