'use client';

import React, { useEffect, useState } from 'react';
import {
  BarChart3,
  FileText,
  Layers,
  HelpCircle,
  ShieldCheck,
  RefreshCw,
  Cpu,
  Database,
  Lock,
  Download,
  History,
  CheckCircle2,
  AlertTriangle,
  XCircle,
} from 'lucide-react';
import { WorkspaceAnalytics } from '@/types';
import { api } from '@/lib/api';

interface AnalyticsPanelProps {
  workspaceId: string;
}

interface HistoryItem {
  id: string;
  item_type: 'qa' | 'claim';
  title: string;
  status: string;
  confidence_score: number;
  citations_count: number;
  created_at: string;
  summary: string;
}

export const AnalyticsPanel: React.FC<AnalyticsPanelProps> = ({ workspaceId }) => {
  const [analytics, setAnalytics] = useState<WorkspaceAnalytics | null>(null);
  const [historyItems, setHistoryItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  const fetchAnalytics = () => {
    if (!workspaceId) return;
    setLoading(true);
    Promise.all([
      api.analytics.get(workspaceId),
      api.history.get(workspaceId, 20),
    ])
      .then(([analyticsData, historyData]) => {
        setAnalytics(analyticsData);
        setHistoryItems(historyData.items as HistoryItem[]);
      })
      .catch((err) => console.error('Failed to load telemetry or history:', err))
      .finally(() => setLoading(false));
  };

  const handleDownloadReport = async () => {
    if (!workspaceId) return;
    setExporting(true);
    try {
      const res = await api.reports.export(workspaceId);
      const blob = new Blob([res.markdown_content], { type: 'text/markdown' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `prooflens_report_${res.workspace_name.toLowerCase().replace(/\s+/g, '_')}.md`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: unknown) {
      alert(`Export failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setExporting(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [workspaceId]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)', maxWidth: 'var(--content-max)', margin: '0 auto', width: '100%' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-3)' }}>
        <div>
          <h3 style={{ fontSize: 'var(--text-lg)', fontWeight: 'var(--weight-bold)' }}>
            Quality & Retrieval Telemetry
          </h3>
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
            Evidence grounding rate, citation validity, and abstention frequency
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <button
            onClick={handleDownloadReport}
            disabled={exporting}
            className="btn-primary"
            style={{ fontSize: 'var(--text-xs)', display: 'inline-flex', alignItems: 'center', gap: 'var(--space-1-5)' }}
          >
            <Download size={14} className={exporting ? 'animate-pulse-glow' : ''} />
            {exporting ? 'Generating Report...' : 'Export Report (.md)'}
          </button>
          <button onClick={fetchAnalytics} disabled={loading} className="btn-secondary" style={{ fontSize: 'var(--text-xs)' }}>
            <RefreshCw size={14} className={loading ? 'animate-pulse-glow' : ''} /> Refresh
          </button>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: 'var(--space-4)',
        }}
      >
        {/* Total Documents */}
        <div className="surface-card" style={{ padding: 'var(--space-5)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 'var(--weight-semibold)', letterSpacing: '0.04em' }}>
              Documents
            </span>
            <FileText size={18} color="var(--color-brand)" />
          </div>
          <div style={{ fontSize: 'var(--text-3xl)', fontWeight: 'var(--weight-bold)', color: 'var(--color-text-primary)' }}>
            {analytics?.total_documents ?? 0}
          </div>
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', marginTop: 'var(--space-1)' }}>
            {analytics?.total_pages ?? 0} total pages extracted
          </p>
        </div>

        {/* Total Chunks */}
        <div className="surface-card" style={{ padding: 'var(--space-5)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 'var(--weight-semibold)', letterSpacing: '0.04em' }}>
              Indexed Chunks
            </span>
            <Layers size={18} color="var(--color-accent)" />
          </div>
          <div style={{ fontSize: 'var(--text-3xl)', fontWeight: 'var(--weight-bold)', color: 'var(--color-text-primary)' }}>
            {analytics?.total_chunks ?? 0}
          </div>
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', marginTop: 'var(--space-1)' }}>
            768-dim embeddings in pgvector
          </p>
        </div>

        {/* Avg Grounding Confidence */}
        <div className="surface-card" style={{ padding: 'var(--space-5)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 'var(--weight-semibold)', letterSpacing: '0.04em' }}>
              Avg Confidence
            </span>
            <ShieldCheck size={18} color="var(--color-success)" />
          </div>
          <div style={{ fontSize: 'var(--text-3xl)', fontWeight: 'var(--weight-bold)', color: 'var(--color-success)' }}>
            {analytics ? `${(analytics.average_confidence * 100).toFixed(1)}%` : '0%'}
          </div>
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', marginTop: 'var(--space-1)' }}>
            Across {analytics?.total_queries ?? 0} executed queries
          </p>
        </div>

        {/* Abstention Rate */}
        <div className="surface-card" style={{ padding: 'var(--space-5)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 'var(--weight-semibold)', letterSpacing: '0.04em' }}>
              Abstention Rate
            </span>
            <HelpCircle size={18} color="var(--color-warning)" />
          </div>
          <div style={{ fontSize: 'var(--text-3xl)', fontWeight: 'var(--weight-bold)', color: 'var(--color-warning)' }}>
            {analytics ? `${(analytics.abstention_rate * 100).toFixed(1)}%` : '0%'}
          </div>
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', marginTop: 'var(--space-1)' }}>
            Refusal on unsupported questions
          </p>
        </div>
      </div>

      {/* Architecture & Verification Guardrails Showcase */}
      <div className="surface-card" style={{ padding: 'var(--space-6)' }}>
        <h4 style={{ fontSize: 'var(--text-md)', fontWeight: 'var(--weight-bold)', marginBottom: 'var(--space-4)' }}>
          Active Verification Architecture & Guardrails
        </h4>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: 'var(--space-4)',
          }}
        >
          <div className="surface-card-subtle" style={{ padding: 'var(--space-4)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
              <Cpu size={16} color="var(--color-brand)" />
              <span style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-bold)' }}>Google Gemini 2.5 Flash</span>
            </div>
            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', lineHeight: 'var(--line-body)' }}>
              Evidence-enclosed prompt generation with &lt;evidence_context&gt; delimiters to prevent prompt injection and force verifiable claims.
            </p>
          </div>

          <div className="surface-card-subtle" style={{ padding: 'var(--space-4)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
              <Database size={16} color="var(--color-accent)" />
              <span style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-bold)' }}>gemini-embedding-2 (768-dim)</span>
            </div>
            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', lineHeight: 'var(--line-body)' }}>
              Elastic output dimension configured to 768 dimensions for optimal pgvector indexing speed and cosine similarity accuracy.
            </p>
          </div>

          <div className="surface-card-subtle" style={{ padding: 'var(--space-4)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
              <Lock size={16} color="var(--color-success)" />
              <span style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-bold)' }}>Strict Tenant Isolation</span>
            </div>
            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', lineHeight: 'var(--line-body)' }}>
              All database records and vector queries enforce workspace_id predicates server-side to guarantee multi-tenant data privacy.
            </p>
          </div>
        </div>
      </div>

      {/* Investigation Audit Trail & History */}
      <div className="surface-card" style={{ padding: 'var(--space-6)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-4)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <History size={18} color="var(--color-brand)" />
            <h4 style={{ fontSize: 'var(--text-md)', fontWeight: 'var(--weight-bold)' }}>
              Investigation Audit Trail
            </h4>
          </div>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
            {historyItems.length} logged sessions
          </span>
        </div>

        {historyItems.length === 0 ? (
          <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: 'var(--text-sm)' }}>
            No investigation sessions logged yet. Ask questions or verify claims to populate this audit trail.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            {historyItems.map((item) => (
              <div
                key={item.id}
                className="surface-card-subtle"
                style={{
                  padding: 'var(--space-4)',
                  display: 'flex',
                  alignItems: 'flex-start',
                  justifyContent: 'space-between',
                  gap: 'var(--space-4)',
                }}
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)', flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
                    <span
                      style={{
                        fontSize: '10px',
                        fontWeight: 'var(--weight-bold)',
                        padding: '2px 8px',
                        borderRadius: 'var(--radius-pill)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.04em',
                        background: item.item_type === 'qa' ? 'rgba(79, 142, 247, 0.15)' : 'rgba(168, 85, 247, 0.15)',
                        color: item.item_type === 'qa' ? 'var(--color-brand)' : 'var(--color-accent)',
                      }}
                    >
                      {item.item_type === 'qa' ? 'Q&A Query' : 'Claim Verification'}
                    </span>
                    <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                      {new Date(item.created_at).toLocaleString()}
                    </span>
                  </div>
                  <h5 style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-semibold)', color: 'var(--color-text-primary)' }}>
                    {item.title}
                  </h5>
                  <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', lineHeight: 'var(--line-body)' }}>
                    {item.summary.length > 200 ? `${item.summary.slice(0, 200)}...` : item.summary}
                  </p>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 'var(--space-1)' }}>
                  <span
                    style={{
                      fontSize: '11px',
                      fontWeight: 'var(--weight-semibold)',
                      padding: '2px 8px',
                      borderRadius: 'var(--radius-pill)',
                      background:
                        item.status.toLowerCase().includes('supported') && !item.status.toLowerCase().includes('partially')
                          ? 'rgba(16, 185, 129, 0.15)'
                          : item.status.toLowerCase().includes('contradicted')
                          ? 'rgba(239, 68, 68, 0.15)'
                          : 'rgba(245, 158, 11, 0.15)',
                      color:
                        item.status.toLowerCase().includes('supported') && !item.status.toLowerCase().includes('partially')
                          ? 'var(--color-success)'
                          : item.status.toLowerCase().includes('contradicted')
                          ? 'var(--color-danger)'
                          : 'var(--color-warning)',
                    }}
                  >
                    {item.status}
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                    {item.citations_count} citation{item.citations_count !== 1 ? 's' : ''}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
