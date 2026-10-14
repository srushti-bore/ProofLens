'use client';

import React, { useState } from 'react';
import {
  GitCompare,
  CheckCircle2,
  AlertTriangle,
  Scale,
  FileText,
  Clock,
} from 'lucide-react';
import { ComparisonResult, Document } from '@/types';
import { api } from '@/lib/api';

interface DocumentComparisonPanelProps {
  documents: Document[];
  workspaceId: string;
}

export const DocumentComparisonPanel: React.FC<DocumentComparisonPanelProps> = ({
  documents,
  workspaceId,
}) => {
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>(
    documents.slice(0, 2).map((d) => d.id)
  );
  const [topic, setTopic] = useState('Architecture, vector embedding dimensions, and database choices');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const toggleDocSelection = (docId: string) => {
    if (selectedDocIds.includes(docId)) {
      setSelectedDocIds(selectedDocIds.filter((id) => id !== docId));
    } else {
      setSelectedDocIds([...selectedDocIds, docId]);
    }
  };

  const handleCompare = async () => {
    if (selectedDocIds.length < 2) {
      setError('Please select at least 2 documents to compare.');
      return;
    }
    if (!topic.trim()) {
      setError('Please provide a comparison topic or question.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await api.comparison.compare(workspaceId, topic, selectedDocIds);
      setResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Cross-document comparison failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)', maxWidth: 'var(--content-max)', margin: '0 auto', width: '100%' }}>
      {/* Configuration Card */}
      <div className="surface-card" style={{ padding: 'var(--space-5)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-4)' }}>
          <GitCompare size={18} color="var(--color-brand)" />
          <h3 style={{ fontSize: 'var(--text-md)', fontWeight: 'var(--weight-bold)' }}>
            Cross-Document Comparison Matrix
          </h3>
        </div>

        {/* Document Selection */}
        <div style={{ marginBottom: 'var(--space-4)' }}>
          <label style={{ fontSize: 'var(--text-xs)', fontWeight: 'var(--weight-semibold)', color: 'var(--color-text-secondary)', display: 'block', marginBottom: 'var(--space-2)' }}>
            Select Documents to Contrast (Minimum 2 required):
          </label>
          <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
            {documents.map((doc) => {
              const isSelected = selectedDocIds.includes(doc.id);
              return (
                <button
                  key={doc.id}
                  onClick={() => toggleDocSelection(doc.id)}
                  style={{
                    padding: 'var(--space-2) var(--space-3)',
                    borderRadius: 'var(--radius-sm)',
                    background: isSelected ? 'var(--color-accent-soft)' : 'var(--color-surface-subtle)',
                    border: isSelected ? '1px solid var(--color-brand)' : '1px solid var(--color-border)',
                    color: isSelected ? 'var(--color-brand)' : 'var(--color-text-secondary)',
                    fontSize: 'var(--text-xs)',
                    fontWeight: isSelected ? 'var(--weight-semibold)' : 'var(--weight-regular)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--space-2)',
                    transition: 'all var(--motion-fast) var(--ease-standard)',
                  }}
                >
                  <FileText size={13} />
                  <span>{doc.filename}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Topic Input */}
        <div>
          <label style={{ fontSize: 'var(--text-xs)', fontWeight: 'var(--weight-semibold)', color: 'var(--color-text-secondary)', display: 'block', marginBottom: 'var(--space-2)' }}>
            Comparison Aspect / Topic:
          </label>
          <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
            <input
              type="text"
              className="input-field"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. Compare data isolation, database, and embedding models"
            />
            <button
              onClick={handleCompare}
              disabled={loading || selectedDocIds.length < 2 || !topic.trim()}
              className="btn-primary"
              style={{ whiteSpace: 'nowrap' }}
            >
              <GitCompare size={15} /> Run Matrix
            </button>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="surface-card animate-entrance" style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
          <Clock size={24} color="var(--color-brand)" style={{ marginBottom: 'var(--space-2)' }} />
          <p style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-semibold)' }}>
            Synthesizing Comparative Matrix Across Target Documents...
          </p>
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', marginTop: 'var(--space-1)' }}>
            Analyzing consensus, contradictions, and definition mismatches
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

      {/* Comparison Matrix Presentation */}
      {result && !loading && (() => {
        const findingsList = result.findings || result.findings_per_document || [];
        const consensusList = result.consensus || result.agreements || [];
        const divergencesList = result.divergences || result.differences || [];
        const scopeList = result.scope_mismatches || result.scope_limitations || [];

        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
            {/* Findings Per Document */}
            <div>
              <h4 style={{ fontSize: 'var(--text-xs)', fontWeight: 'var(--weight-bold)', color: 'var(--color-text-muted)', textTransform: 'uppercase', marginBottom: 'var(--space-3)', letterSpacing: '0.04em' }}>
                Findings Per Document
              </h4>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: `repeat(auto-fit, minmax(300px, 1fr))`,
                  gap: 'var(--space-4)',
                }}
              >
                {findingsList.map((f, i) => {
                  const pages = f.page_citations || (f.citations ? f.citations.map((c) => c.page_number) : []);
                  return (
                    <div key={i} className="surface-card" style={{ padding: 'var(--space-4)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                          <FileText size={16} color="var(--color-brand)" />
                          <span style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-bold)' }}>
                            {f.document_name || f.filename || 'Document'}
                          </span>
                        </div>
                        <div style={{ display: 'flex', gap: 'var(--space-1)' }}>
                          {pages.map((p, pIdx) => (
                            <span
                              key={pIdx}
                              style={{
                                fontSize: '11px',
                                fontWeight: 'var(--weight-semibold)',
                                padding: '0.1rem 0.4rem',
                                borderRadius: 'var(--radius-xs)',
                                background: 'var(--color-surface-subtle)',
                                color: 'var(--color-brand)',
                                border: '1px solid var(--color-border)',
                              }}
                            >
                              p. {p}
                            </span>
                          ))}
                        </div>
                      </div>
                      <p style={{ fontSize: 'var(--text-xs)', lineHeight: 'var(--line-body)', color: 'var(--color-text-secondary)' }}>
                        {f.findings || f.summary}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Tri-Column Matrix: Consensus, Divergences, Scope Mismatches */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: 'var(--space-4)',
              }}
            >
              {/* Consensus */}
              <div className="surface-card" style={{ padding: 'var(--space-4)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-3)' }}>
                  <CheckCircle2 size={16} color="var(--color-success)" />
                  <span style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-bold)', color: 'var(--color-success)' }}>
                    Consensus ({consensusList.length})
                  </span>
                </div>
                <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                  {consensusList.map((c, i) => (
                    <li
                      key={i}
                      style={{
                        fontSize: 'var(--text-xs)',
                        color: 'var(--color-text-secondary)',
                        lineHeight: 'var(--line-body)',
                        padding: 'var(--space-2) var(--space-3)',
                        background: 'var(--color-success-soft)',
                        borderRadius: 'var(--radius-xs)',
                        border: '1px solid rgba(16, 185, 129, 0.2)',
                      }}
                    >
                      • {c}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Divergences */}
              <div className="surface-card" style={{ padding: 'var(--space-4)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-3)' }}>
                  <AlertTriangle size={16} color="var(--color-warning)" />
                  <span style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-bold)', color: 'var(--color-warning)' }}>
                    Divergences & Conflicts ({divergencesList.length})
                  </span>
                </div>
                <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                  {divergencesList.map((d, i) => (
                    <li
                      key={i}
                      style={{
                        fontSize: 'var(--text-xs)',
                        color: 'var(--color-text-secondary)',
                        lineHeight: 'var(--line-body)',
                        padding: 'var(--space-2) var(--space-3)',
                        background: 'var(--color-warning-soft)',
                        borderRadius: 'var(--radius-xs)',
                        border: '1px solid rgba(245, 158, 11, 0.2)',
                      }}
                    >
                      • {d}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Scope Mismatches */}
              <div className="surface-card" style={{ padding: 'var(--space-4)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-3)' }}>
                  <Scale size={16} color="var(--color-accent)" />
                  <span style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-bold)', color: 'var(--color-accent)' }}>
                    Scope Nuances ({scopeList.length})
                  </span>
                </div>
                <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                  {scopeList.map((s, i) => (
                    <li
                      key={i}
                      style={{
                        fontSize: 'var(--text-xs)',
                        color: 'var(--color-text-secondary)',
                        lineHeight: 'var(--line-body)',
                        padding: 'var(--space-2) var(--space-3)',
                        background: 'var(--color-accent-soft)',
                        borderRadius: 'var(--radius-xs)',
                        border: '1px solid rgba(99, 102, 241, 0.2)',
                      }}
                    >
                      • {s}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
};
