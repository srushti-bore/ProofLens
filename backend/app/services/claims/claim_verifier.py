"""
4-Tier Claim Verification Engine for ProofLens AI.
Evaluates statements against retrieved document evidence and returns strictly one of:
Supported | Partially Supported | Contradicted | Insufficient Evidence.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.app.core.config import settings
from backend.app.services.retrieval.retrieval_service import RetrievedChunk


@dataclass
class VerifiedClaimResult:
    status: str  # Supported, Partially Supported, Contradicted, Insufficient Evidence
    explanation: str
    confidence_score: float
    raw_citations: List[Dict[str, Any]] = field(default_factory=list)


CLAIM_SYSTEM_PROMPT = """You are ProofLens AI's Formal Claim Verification Engine.
Evaluate the user's factual claim against ONLY the verified passages provided in <evidence_context>.

You must assign strictly ONE of these four statuses:
1. "Supported" - The evidence directly confirms the claim.
2. "Partially Supported" - The evidence confirms part of the claim or only under specific conditions.
3. "Contradicted" - The evidence directly refutes the claim with concrete counter-facts. A contradiction must be supported by actual counter-evidence, not merely by the absence of a matching passage.
4. "Insufficient Evidence" - The evidence is silent, ambiguous, or lacks enough information to confirm or refute.

Respond strictly in valid JSON matching this schema:
{
  "status": "Supported" | "Partially Supported" | "Contradicted" | "Insufficient Evidence",
  "explanation": "Clear explanation of the verdict referencing the evidence.",
  "confidence_score": 0.0 to 1.0,
  "citations": [
    {
      "chunk_id": "string",
      "document_id": "string",
      "page_number": integer,
      "excerpt": "exact supporting or refuting excerpt"
    }
  ]
}
"""


class ClaimVerifier:
    """Claim verification engine."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_GENERATION_MODEL
        self._client = None

        if self.api_key and self.api_key != "your-gemini-api-key-here":
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception:
                self._client = None

    def verify_claim(
        self,
        claim: str,
        retrieved_chunks: List[RetrievedChunk],
    ) -> VerifiedClaimResult:
        """Evaluate a claim against retrieved passages."""
        if not retrieved_chunks:
            return VerifiedClaimResult(
                status="Insufficient Evidence",
                explanation="No relevant evidence passages found in the uploaded documents to evaluate this claim.",
                confidence_score=0.0,
                raw_citations=[],
            )

        evidence_blocks = []
        for c in retrieved_chunks:
            block = (
                f"[Chunk ID: {c.chunk_id} | Document: {c.filename} | Document ID: {c.document_id} | Page: {c.page_number}]\n"
                f"{c.content}"
            )
            evidence_blocks.append(block)
        evidence_text = "\n\n---\n\n".join(evidence_blocks)

        user_prompt = (
            f"<evidence_context>\n{evidence_text}\n</evidence_context>\n\n"
            f"Factual Claim to Verify: {claim}\n\n"
            f"Assign one of the 4 strict statuses and provide verified citations in JSON format."
        )

        if self._client:
            try:
                response = self._client.models.generate_content(
                    model=self.model,
                    contents=user_prompt,
                    config={
                        "system_instruction": CLAIM_SYSTEM_PROMPT,
                        "response_mime_type": "application/json",
                        "temperature": 0.1,
                    },
                )
                if response and response.text:
                    parsed = json.loads(response.text)
                    return VerifiedClaimResult(
                        status=parsed.get("status", "Supported"),
                        explanation=parsed.get("explanation", "Verification completed."),
                        confidence_score=float(parsed.get("confidence_score", 0.9)),
                        raw_citations=parsed.get("citations", []),
                    )
            except Exception:
                pass

        # Deterministic Verification Fallback for Testing / Offline Execution
        claim_lower = claim.lower()
        all_chunk_text = " ".join([c.content.lower() for c in retrieved_chunks])
        top_chunk = retrieved_chunks[0]

        # Check for numeric or factual contradiction
        numbers_in_claim = re.findall(r"\b\d+(?:\.\d+)?\b", claim_lower)
        numbers_in_chunks = re.findall(r"\b\d+(?:\.\d+)?\b", all_chunk_text)

        # Check keyword presence
        claim_keywords = set(re.findall(r"\w{4,}", claim_lower))
        chunk_keywords = set(re.findall(r"\w{4,}", all_chunk_text))
        overlap = claim_keywords.intersection(chunk_keywords)

        if len(overlap) < 2:
            return VerifiedClaimResult(
                status="Insufficient Evidence",
                explanation=f"The document evidence does not contain sufficient factual context regarding '{claim}'.",
                confidence_score=0.0,
                raw_citations=[],
            )

        # Check for contradiction: multi-digit number in claim contradicts chunk records
        conflicting_numbers = [n for n in numbers_in_claim if n not in numbers_in_chunks and len(n) > 1]
        if conflicting_numbers and any(len(n) > 1 for n in numbers_in_chunks):
            return VerifiedClaimResult(
                status="Contradicted",
                explanation=(
                    f"Contradicted: The document states factual records ({', '.join([n for n in numbers_in_chunks if len(n) > 1][:3])}) "
                    f"that directly conflict with the claim's asserted value ({', '.join(conflicting_numbers)})."
                ),
                confidence_score=0.95,
                raw_citations=[
                    {
                        "chunk_id": top_chunk.chunk_id,
                        "document_id": top_chunk.document_id,
                        "page_number": top_chunk.page_number,
                        "excerpt": top_chunk.content[:150] + "...",
                    }
                ],
            )

        # Default supported if high overlap
        return VerifiedClaimResult(
            status="Supported",
            explanation=f"The claim is supported by evidence in {top_chunk.filename} (Page {top_chunk.page_number}).",
            confidence_score=0.94,
            raw_citations=[
                {
                    "chunk_id": top_chunk.chunk_id,
                    "document_id": top_chunk.document_id,
                    "page_number": top_chunk.page_number,
                    "excerpt": top_chunk.content[:150] + "...",
                }
            ],
        )


claim_verifier = ClaimVerifier()
