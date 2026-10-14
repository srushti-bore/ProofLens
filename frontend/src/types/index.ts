/**
 * TypeScript types for ProofLens AI frontend.
 * Strictly aligned with backend Pydantic schemas.
 */

export interface User {
  id: string;
  email: string;
  full_name?: string | null;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user?: User;
  expires_in?: number;
}

export interface Workspace {
  id: string;
  name: string;
  description?: string | null;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: string;
  workspace_id: string;
  filename: string;
  file_size: number;
  file_hash?: string | null;
  page_count: number;
  mime_type: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  error_message?: string | null;
  created_at: string;
}

export interface DocumentPage {
  id: string;
  document_id: string;
  page_number: number;
  text_content: string;
  char_count: number;
  created_at: string;
}

export interface Citation {
  id?: string;
  chunk_id: string;
  document_id: string;
  document_name?: string;
  filename?: string;
  page_number: number;
  excerpt: string;
  is_validated: boolean;
}

export interface QAAnswer {
  id?: string;
  query_id: string;
  conversation_id?: string;
  conversation_title?: string;
  question?: string;
  answer: string;
  status: string;
  confidence_score: number;
  retrieved_chunks_count?: number;
  citations: Citation[];
}

export type ClaimStatus = 'Supported' | 'Partially Supported' | 'Contradicted' | 'Insufficient Evidence';

export interface ClaimCitation {
  id?: string;
  chunk_id: string;
  document_id: string;
  document_name?: string;
  filename?: string;
  page_number: number;
  excerpt: string;
  is_validated?: boolean;
}

export interface ClaimVerificationResult {
  id?: string;
  claim_id?: string;
  claim: string;
  status: ClaimStatus;
  explanation: string;
  confidence_score?: number;
  citations: ClaimCitation[];
}

export interface DocumentFinding {
  document_id: string;
  document_name?: string;
  filename?: string;
  findings?: string;
  summary?: string;
  citations?: ClaimCitation[];
  page_citations?: number[];
}

export interface ComparisonResult {
  topic: string;
  findings_per_document?: DocumentFinding[];
  findings?: DocumentFinding[];
  agreements?: string[];
  consensus?: string[];
  differences?: string[];
  divergences?: string[];
  scope_limitations?: string[];
  scope_mismatches?: string[];
  synthesis_summary?: string;
}

export interface WorkspaceAnalytics {
  workspace_id: string;
  total_documents: number;
  total_pages: number;
  total_chunks: number;
  total_queries: number;
  total_claims_verified: number;
  average_confidence: number;
  abstention_rate: number;
}

export interface RetrievalChunk {
  chunk_id: string;
  document_id: string;
  page_number: number;
  chunk_index: number;
  content: string;
  similarity_score: number;
}

export interface HistoryItem {
  id: string;
  item_type: 'qa' | 'claim';
  title: string;
  status: string;
  confidence_score: number;
  citations_count: number;
  created_at: string;
  summary: string;
  details: {
    conversation_id?: string;
    message_count?: number;
    answer?: string;
    explanation?: string;
    citations?: Citation[];
    [key: string]: unknown;
  };
}

export interface ConversationTurn {
  query_id: string;
  question: string;
  answer: string;
  status: string;
  confidence_score: number;
  retrieved_chunks_count: number;
  citations: Citation[];
  created_at: string;
}

export interface ConversationDetail {
  id: string;
  workspace_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  turns: ConversationTurn[];
}

export interface ConversationSummary {
  id: string;
  workspace_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message_preview?: string;
}
