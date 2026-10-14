/**
 * Centralized, type-safe API client for ProofLens AI.
 * Communicates with FastAPI backend under /api/v1/*.
 * Strictly isolates secrets server-side; handles auth tokens from browser storage.
 */

import {
  ClaimVerificationResult,
  ComparisonResult,
  ConversationDetail,
  ConversationSummary,
  Document,
  DocumentPage,
  QAAnswer,
  RetrievalChunk,
  TokenResponse,
  User,
  Workspace,
  WorkspaceAnalytics,
} from '@/types';

const rawApiUrl = (
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
).replace(/\/+$/, '');

const API_BASE_URL = rawApiUrl.endsWith('/api/v1')
  ? rawApiUrl
  : `${rawApiUrl}/api/v1`;

class ApiClient {
  private tokenKey = 'prooflens_auth_token';

  public getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(this.tokenKey);
  }

  public setToken(token: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem(this.tokenKey, token);
  }

  public clearToken(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(this.tokenKey);
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string>),
    };

    const token = this.getToken();
    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Default to application/json unless body is FormData
    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        let errorMessage = `Request failed with status ${response.status}`;
        try {
          const errorJson = await response.json();
          if (Array.isArray(errorJson.detail)) {
            // Format Pydantic validation errors cleanly
            errorMessage = errorJson.detail
              .map((e: { msg?: string; message?: string }) => e.msg || e.message || JSON.stringify(e))
              .join('; ');
          } else if (typeof errorJson.detail === 'string') {
            errorMessage = errorJson.detail;
          } else if (errorJson.message) {
            errorMessage = errorJson.message;
          } else if (errorJson.detail && typeof errorJson.detail === 'object') {
            errorMessage = JSON.stringify(errorJson.detail);
          }
        } catch {
          // Fall back to status text
          errorMessage = response.statusText || errorMessage;
        }

        if (response.status === 401) {
          // Token expired or invalid
          this.clearToken();
        }

        throw new Error(errorMessage);
      }

      if (response.status === 204) {
        return {} as T;
      }

      return (await response.json()) as T;
    } catch (err: unknown) {
      if (err instanceof Error) {
        throw err;
      }
      throw new Error('An unknown network error occurred');
    }
  }

  // Auth Endpoints
  public auth = {
    register: (email: string, password: string, fullName?: string) =>
      this.request<TokenResponse>('/auth/register', {
        method: 'POST',
        body: JSON.stringify({
          email: email.trim().toLowerCase(),
          password,
          full_name: fullName?.trim() || undefined,
        }),
      }),

    login: (email: string, password: string) =>
      this.request<TokenResponse>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          email: email.trim().toLowerCase(),
          password,
        }),
      }),

    getMe: () => this.request<User>('/auth/me'),
  };

  // Workspace Endpoints
  public workspaces = {
    list: () => this.request<Workspace[]>('/workspaces'),
    create: (name: string, description?: string) =>
      this.request<Workspace>('/workspaces', {
        method: 'POST',
        body: JSON.stringify({ name, description }),
      }),
    get: (id: string) => this.request<Workspace>(`/workspaces/${id}`),
  };

  // Documents Endpoints
  public documents = {
    list: (workspaceId: string) =>
      this.request<Document[]>(`/workspaces/${workspaceId}/documents`),

    upload: (workspaceId: string, file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return this.request<Document>(`/workspaces/${workspaceId}/documents/upload`, {
        method: 'POST',
        body: formData,
      });
    },

    getPages: (workspaceId: string, documentId: string) =>
      this.request<DocumentPage[]>(
        `/workspaces/${workspaceId}/documents/${documentId}/pages`
      ),

    getFileUrl: (workspaceId: string, documentId: string) =>
      `${API_BASE_URL}/workspaces/${workspaceId}/documents/${documentId}/file`,

    delete: (workspaceId: string, documentId: string) =>
      this.request<void>(
        `/workspaces/${workspaceId}/documents/${documentId}`,
        { method: 'DELETE' }
      ),
  };

  // Retrieval & Vector Search
  public retrieval = {
    search: (
      workspaceId: string,
      query: string,
      topK: number = 5,
      similarityThreshold: number = 0.35,
      documentIds?: string[]
    ) =>
      this.request<RetrievalChunk[]>(
        `/workspaces/${workspaceId}/retrieval/search`,
        {
          method: 'POST',
          body: JSON.stringify({
            query,
            top_k: topK,
            similarity_threshold: similarityThreshold,
            document_ids: documentIds,
          }),
        }
      ),
  };

  // Grounded Q&A
  public qa = {
    ask: (
      workspaceId: string,
      query: string,
      documentIds?: string[],
      conversationId?: string
    ) =>
      this.request<QAAnswer>(`/workspaces/${workspaceId}/qa/ask`, {
        method: 'POST',
        body: JSON.stringify({
          question: query,
          query,
          document_ids: documentIds && documentIds.length > 0 ? documentIds : undefined,
          conversation_id: conversationId,
        }),
      }),
  };

  // Persistent Conversation Threads
  public conversations = {
    list: (workspaceId: string, query?: string) => {
      const qParam = query && query.trim() ? `?query=${encodeURIComponent(query.trim())}` : '';
      return this.request<ConversationSummary[]>(`/workspaces/${workspaceId}/conversations${qParam}`);
    },
    get: (workspaceId: string, conversationId: string) =>
      this.request<ConversationDetail>(`/workspaces/${workspaceId}/conversations/${conversationId}`),
    delete: (workspaceId: string, conversationId: string) =>
      this.request<void>(`/workspaces/${workspaceId}/conversations/${conversationId}`, {
        method: 'DELETE',
      }),
  };

  // 4-Tier Claim Verification
  public claims = {
    verify: (workspaceId: string, claim: string, documentIds?: string[]) =>
      this.request<ClaimVerificationResult>(
        `/workspaces/${workspaceId}/claims/verify`,
        {
          method: 'POST',
          body: JSON.stringify({
            claim,
            document_ids: documentIds && documentIds.length > 0 ? documentIds : undefined,
          }),
        }
      ),
  };

  // Cross-Document Comparison
  public comparison = {
    compare: (workspaceId: string, topic: string, documentIds: string[]) =>
      this.request<ComparisonResult>(
        `/workspaces/${workspaceId}/comparison/compare`,
        {
          method: 'POST',
          body: JSON.stringify({
            topic,
            document_ids: documentIds,
          }),
        }
      ),
  };

  // Workspace Analytics
  public analytics = {
    get: (workspaceId: string) =>
      this.request<WorkspaceAnalytics>(`/workspaces/${workspaceId}/analytics`),
  };

  // Investigation History
  public history = {
    get: (workspaceId: string, limit: number = 50, query?: string) => {
      const qParam = query && query.trim() ? `&query=${encodeURIComponent(query.trim())}` : '';
      return this.request<{
        workspace_id: string;
        total_items: number;
        items: Array<{
          id: string;
          item_type: 'qa' | 'claim';
          title: string;
          status: string;
          confidence_score: number;
          citations_count: number;
          created_at: string;
          summary: string;
          details: Record<string, unknown>;
        }>;
      }>(`/workspaces/${workspaceId}/history?limit=${limit}${qParam}`);
    },
  };

  // Report Export
  public reports = {
    export: (workspaceId: string) =>
      this.request<{
        workspace_id: string;
        workspace_name: string;
        generated_at: string;
        format: string;
        markdown_content: string;
      }>(`/workspaces/${workspaceId}/reports/export`),
    getDownloadUrl: (workspaceId: string) =>
      `${API_BASE_URL}/workspaces/${workspaceId}/reports/export?download=true`,
  };
}

export const api = new ApiClient();
