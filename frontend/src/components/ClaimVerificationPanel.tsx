'use client';

import React, { useState } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  FileText,
  Clock,
  Filter,
  ChevronRight,
} from 'lucide-react';
import { Citation, ClaimStatus, ClaimVerificationResult, Document } from '@/types';
import { api } from '@/lib/api';

interface ClaimVerificationPanelProps {
  documents: Document[];
  workspaceId: string;
  onOpenCitation: (citation: Citation) => void;
}

export const ClaimVerificationPanel: React.FC<ClaimVerificationPanelProps> = ({
  documents,
  workspaceId,
  onOpenCitation,
}) => {
  const [claimText, setClaimText] = useState('');
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ClaimVerificationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const benchmarkClaims = [
    {
      label: 'Supported Claim',
      claim: 'ProofLens AI uses Python 3.13, FastAPI, and PostgreSQL 18 with pgvector.',
    },
    {
      label: 'Contradicted Claim',
      claim: 'ProofLens AI was founded in 1977 as a mainframe system.',
    },
    {
      label: 'Insufficient Evidence',
      claim: 'The platform integrates autonomous drone delivery and satellite tracking.',
    },
  ];

  const handleVerify = async (textToVerify?: string) => {
    const text = (textToVerify || claimText).trim();
    if (!text || loading) return;

    setLoading(true);
    setError(null);

    try {
      const res = await api.claims.verify(
        workspaceId,
        text,
        selectedDocIds.length > 0 ? selectedDocIds : undefined
      );
      setResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Claim verification failed');
    } finally {
      setLoading(false);
    }
  };

  const getStatusPresentation = (status: ClaimStatus) => {
    switch (status) {
      case 'Supported':
        return {
          icon: CheckCircle2,
          bg: 'var(--color-success-soft)',
          border: 'rgba(16, 185, 129, 0.35)',
          color: 'var(--color-success)',
          label: 'Supported',
          description: 'Verified true. Clear evidence in workspace documents directly corroborates this claim.',
        };
      case 'Partially Supported':
        return {
          icon: AlertTriangle,
          bg: 'var(--color-warning-soft)',
          border: 'rgba(245, 158, 11, 0.35)',
          color: 'var(--color-warning)',
          label: 'Partially Supported',
          description: 'Nuanced. The claim holds under specific stated conditions or definitions.',
        };
      case 'Contradicted':
        return {
          icon: XCircle,
          bg: 'var(--color-danger-soft)',
          border: 'rgba(239, 68, 68, 0.35)',
          color: 'var(--color-danger)',
          label: 'Contradicted',
          description: 'Refuted. Retrieved passages explicitly conflict with or contradict this claim.',
        };
      case 'Insufficient Evidence':
      default:
        return {
          icon: HelpCircle,
          bg: 'var(--color-surface-subtle)',
          border: 'var(--color-border-strong)',
          color: 'var(--color-text-muted)',
          label: 'Insufficient Evidence',
          description: 'Unknown. Workspace documents contain no evidence to confirm or refute this assertion.',
        };
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)', maxWidth: 'var(--reading-max)', margin: '0 auto', width: '100%' }}>
      {/* Claim Evaluation Input Card */}
      <div className="surface-card" style={{ padding: 'var(--space-5)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <ShieldCheck size={18} color="var(--color-brand)" />
            <h3 style={{ fontSize: 'var(--text-md)', fontWeight: 'var(--weight-bold)' }}>
              4-Tier Claim Verification Engine
            </h3>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <Filter size={13} color="var(--color-text-muted)" />
            <select
              style={{
                background: 'var(--color-surface-subtle)',
                border: '1px solid var(--color-border)',
                color: 'var(--color-text-secondary)',
                fontSize: 'var(--text-xs)',
                padding: 'var(--space-1) var(--space-2)',
                borderRadius: 'var(--radius-xs)',
                outline: 'none',
              }}
              value={selectedDocIds[0] || ''}
              onChange={(e) => setSelectedDocIds(e.target.value ? [e.target.value] : [])}
              aria-label="Filter target documents"
            >
              <option value="">All Documents ({documents.length})</option>
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.filename}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div style={{ position: 'relative' }}>
          <textarea
            className="input-field"
            rows={3}
            style={{
              resize: 'none',
              paddingRight: '7rem',
              lineHeight: 'var(--line-body)',
              fontSize: 'var(--text-sm)',
            }}
            placeholder="Input a factual assertion to verify against the document library..."
            value={claimText}
            onChange={(e) => setClaimText(e.target.value)}
          />
          <button
            onClick={() => handleVerify()}
            disabled={loading || !claimText.trim()}
            className="btn-primary"
            style={{
              position: 'absolute',
              right: 'var(--space-2)',
              bottom: 'var(--space-2)',
              padding: 'var(--space-2) var(--space-3)',
              fontSize: 'var(--text-xs)',
            }}
          >
            <ShieldCheck size={14} /> Verify Claim
          </button>
        </div>

        {/* Benchmark Chips */}
        <div style={{ marginTop: 'var(--space-3)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Benchmark Presets:</span>
          {benchmarkClaims.map((item, idx) => (
            <button
              key={idx}
              onClick={() => {
                setClaimText(item.claim);
                handleVerify(item.claim);
              }}
              className="suggestion-chip"
            >
              <span style={{ color: 'var(--color-brand)', fontWeight: 'var(--weight-semibold)' }}>{item.label}:</span>{' '}
              {item.claim.substring(0, 32)}...
            </button>
          ))}
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="surface-card animate-entrance" style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
          <Clock size={24} color="var(--color-brand)" style={{ marginBottom: 'var(--space-2)' }} />
          <p style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-semibold)' }}>
            Evaluating Evidence Polarity & Vector Overlap...
          </p>
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', marginTop: 'var(--space-1)' }}>
            Classifying into Supported, Partially Supported, Contradicted, or Insufficient Evidence
          </p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div
          style={{
            padding: 'var(--space-3) var(--space-4)',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--color-danger-soft)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: 'var(--color-danger)',
            fontSize: 'var(--text-xs)',
          }}
        >
          {error}
        </div>
      )}

      {/* Verification Result Card */}
      {result && !loading && (
        <div className="surface-card animate-entrance" style={{ padding: 'var(--space-6)' }}>
          {(() => {
            const statusConfig = getStatusPresentation(result.status);
            const StatusIcon = statusConfig.icon;
            return (
              <>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: 'var(--space-4)',
                    paddingBottom: 'var(--space-4)',
                    borderBottom: '1px solid var(--color-border)',
                  }}
                >
                  <div>
                    <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                      Verification Status
                    </span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginTop: 'var(--space-1)' }}>
                      <div
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 'var(--space-2)',
                          padding: 'var(--space-2) var(--space-4)',
                          borderRadius: 'var(--radius-sm)',
                          background: statusConfig.bg,
                          border: `1px solid ${statusConfig.border}`,
                          color: statusConfig.color,
                          fontSize: 'var(--text-md)',
                          fontWeight: 'var(--weight-bold)',
                        }}
                      >
                        <StatusIcon size={18} />
                        <span>{statusConfig.label}</span>
                      </div>
                    </div>
                  </div>

                  <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', maxWidth: '320px', textAlign: 'right', lineHeight: 'var(--line-body)' }}>
                    {statusConfig.description}
                  </p>
                </div>

                <div style={{ marginBottom: 'var(--space-4)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontWeight: 'var(--weight-semibold)', textTransform: 'uppercase', marginBottom: 'var(--space-1)' }}>
                    Evaluated Assertion
                  </div>
                  <div
                    style={{
                      fontSize: 'var(--text-sm)',
                      fontWeight: 'var(--weight-medium)',
                      color: 'var(--color-text-primary)',
                      padding: 'var(--space-3) var(--space-4)',
                      background: 'var(--color-surface-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--color-border)',
                    }}
                  >
                    &ldquo;{result.claim}&rdquo;
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontWeight: 'var(--weight-semibold)', textTransform: 'uppercase', marginBottom: 'var(--space-1)' }}>
                    Evidence Rationale & Context
                  </div>
                  <p style={{ fontSize: 'var(--text-sm)', lineHeight: 'var(--line-body)', color: 'var(--color-text-secondary)' }}>
                    {result.explanation}
                  </p>
                </div>

                {/* Supporting Citations */}
                {result.citations && result.citations.length > 0 && (
                  <div style={{ marginTop: 'var(--space-5)', paddingTop: 'var(--space-4)', borderTop: '1px solid var(--color-border)' }}>
                    <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontWeight: 'var(--weight-semibold)', textTransform: 'uppercase', marginBottom: 'var(--space-2)' }}>
                      Supporting Citations ({result.citations.length})
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                      {result.citations.map((c, i) => (
                        <div
                          key={i}
                          onClick={() =>
                            onOpenCitation({
                              ...c,
                              is_validated: true,
                            })
                          }
                          style={{
                            padding: 'var(--space-3) var(--space-4)',
                            borderRadius: 'var(--radius-sm)',
                            backgroundColor: 'var(--color-surface-subtle)',
                            border: '1px solid var(--color-border)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            cursor: 'pointer',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                            <FileText size={15} color="var(--color-brand)" />
                            <div>
                              <div style={{ fontSize: 'var(--text-xs)', fontWeight: 'var(--weight-semibold)', color: 'var(--color-text-primary)' }}>
                                {c.document_name || c.filename || 'Document'} • Page {c.page_number}
                              </div>
                              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                                &ldquo;{c.excerpt}&rdquo;
                              </div>
                            </div>
                          </div>
                          <ChevronRight size={14} color="var(--color-text-muted)" />
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            );
          })()}
        </div>
      )}
    </div>
  );
};
