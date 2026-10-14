'use client';

import React, { useEffect, useState } from 'react';
import {
  X,
  ShieldCheck,
  FileText,
  Bookmark,
  ExternalLink,
  BookOpen,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { Citation, DocumentPage } from '@/types';
import { api } from '@/lib/api';

interface CitationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  citation: Citation | null;
  workspaceId: string;
}

export const CitationDrawer: React.FC<CitationDrawerProps> = ({
  isOpen,
  onClose,
  citation,
  workspaceId,
}) => {
  const [pages, setPages] = useState<DocumentPage[]>([]);
  const [loadingPages, setLoadingPages] = useState(false);

  useEffect(() => {
    if (!isOpen || !citation || !workspaceId) return;

    let isMounted = true;
    setLoadingPages(true);

    api.documents
      .getPages(workspaceId, citation.document_id)
      .then((data) => {
        if (isMounted) setPages(data);
      })
      .catch((err) => {
        console.error('Failed to load document pages:', err);
      })
      .finally(() => {
        if (isMounted) setLoadingPages(false);
      });

    return () => {
      isMounted = false;
    };
  }, [isOpen, citation, workspaceId]);

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !citation) return null;

  const targetPage = pages.find((p) => p.page_number === citation.page_number);
  const pdfUrl = api.documents.getFileUrl(workspaceId, citation.document_id);

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 90,
        display: 'flex',
        justifyContent: 'flex-end',
        backgroundColor: 'rgba(17, 24, 39, 0.45)',
        backdropFilter: 'blur(6px)',
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-label="Citation Source Inspection Drawer"
    >
      <div
        className="animate-entrance"
        style={{
          width: '100%',
          maxWidth: 'var(--source-panel-width)',
          height: '100%',
          backgroundColor: 'var(--color-surface)',
          borderLeft: '1px solid var(--color-border)',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: 'var(--shadow-dialog)',
          overflow: 'hidden',
          transition: 'transform var(--motion-slow) var(--ease-emphasized)',
        }}
      >
        {/* Drawer Header */}
        <div
          style={{
            padding: 'var(--space-4) var(--space-5)',
            borderBottom: '1px solid var(--color-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: 'var(--color-surface-subtle)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: 'var(--radius-xs)',
                background: 'var(--color-accent-soft)',
                border: '1px solid rgba(99, 102, 241, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <ShieldCheck size={17} color="var(--color-link)" />
            </div>
            <div>
              <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-bold)', color: 'var(--color-text-primary)' }}>
                Source Provenance
              </h3>
              <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                Page-level verification & extracted excerpt
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="btn-ghost"
            style={{ padding: 'var(--space-1)' }}
            aria-label="Close Source Drawer"
          >
            <X size={18} />
          </button>
        </div>

        {/* Drawer Content */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: 'var(--space-5)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-5)',
          }}
        >
          {/* Metadata Card */}
          <div className="surface-card-subtle" style={{ padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <FileText size={16} color="var(--color-brand)" />
                <span style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-semibold)', color: 'var(--color-text-primary)' }}>
                  {citation.document_name || citation.filename || 'Document'}
                </span>
              </div>
              <span
                style={{
                  fontSize: 'var(--text-xs)',
                  fontWeight: 'var(--weight-semibold)',
                  padding: 'var(--space-1) var(--space-2)',
                  borderRadius: 'var(--radius-xs)',
                  background: 'var(--color-surface-elevated)',
                  color: 'var(--color-brand)',
                  border: '1px solid var(--color-border-strong)',
                }}
              >
                Page {citation.page_number}
              </span>
            </div>

            {/* Validation State Badge */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-2)',
                padding: 'var(--space-2) var(--space-3)',
                borderRadius: 'var(--radius-xs)',
                backgroundColor: citation.is_validated ? 'var(--color-success-soft)' : 'var(--color-warning-soft)',
                border: `1px solid ${citation.is_validated ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
                color: citation.is_validated ? 'var(--color-success)' : 'var(--color-warning)',
                fontSize: 'var(--text-xs)',
                fontWeight: 'var(--weight-semibold)',
              }}
            >
              {citation.is_validated ? (
                <>
                  <CheckCircle2 size={15} />
                  <span>Verified Ground Truth Match (Confirmed In Vector Chunks)</span>
                </>
              ) : (
                <>
                  <AlertTriangle size={15} />
                  <span>Unverified Citation Reference</span>
                </>
              )}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
              <span>Chunk ID: {citation.chunk_id ? citation.chunk_id.substring(0, 14) + '...' : 'Direct Page'}</span>
              <a
                href={pdfUrl}
                target="_blank"
                rel="noreferrer"
                style={{ color: 'var(--color-link)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 'var(--space-1)', fontWeight: 'var(--weight-medium)' }}
              >
                Open Original PDF <ExternalLink size={12} />
              </a>
            </div>
          </div>

          {/* Exact Supporting Excerpt */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-1)', marginBottom: 'var(--space-2)', fontSize: 'var(--text-xs)', fontWeight: 'var(--weight-semibold)', color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              <Bookmark size={13} color="var(--color-brand)" />
              <span>Exact Supporting Excerpt</span>
            </div>
            <div
              style={{
                padding: 'var(--space-4)',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--color-accent-soft)',
                border: '1px solid rgba(99, 102, 241, 0.25)',
                color: 'var(--color-text-primary)',
                fontSize: 'var(--text-sm)',
                lineHeight: 'var(--line-body)',
              }}
            >
              &ldquo;{citation.excerpt}&rdquo;
            </div>
          </div>

          {/* Page Context (PyMuPDF Full Text Extraction) */}
          <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-1)', fontSize: 'var(--text-xs)', fontWeight: 'var(--weight-semibold)', color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                <BookOpen size={13} color="var(--color-accent)" />
                <span>Page {citation.page_number} Full Text Context</span>
              </div>
              {targetPage && (
                <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                  {targetPage.char_count} chars
                </span>
              )}
            </div>

            <div
              style={{
                flex: 1,
                minHeight: '220px',
                maxHeight: '340px',
                overflowY: 'auto',
                padding: 'var(--space-4)',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--color-surface-subtle)',
                border: '1px solid var(--color-border)',
                color: 'var(--color-text-secondary)',
                fontSize: 'var(--text-xs)',
                lineHeight: 'var(--line-relaxed)',
                fontFamily: 'var(--font-mono)',
                whiteSpace: 'pre-wrap',
              }}
            >
              {loadingPages ? (
                <div style={{ textAlign: 'center', padding: 'var(--space-4)', color: 'var(--color-text-muted)' }}>
                  Loading page context from server...
                </div>
              ) : targetPage ? (
                targetPage.text_content
              ) : (
                <div style={{ color: 'var(--color-text-muted)' }}>
                  Page {citation.page_number} extracted text is ready. Open Original PDF to view original page formatting.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Drawer Footer Actions */}
        <div
          style={{
            padding: 'var(--space-3) var(--space-5)',
            borderTop: '1px solid var(--color-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            gap: 'var(--space-3)',
            backgroundColor: 'var(--color-surface-subtle)',
          }}
        >
          <button onClick={onClose} className="btn-secondary" style={{ fontSize: 'var(--text-xs)' }}>
            Close Inspection
          </button>
          <a
            href={pdfUrl}
            target="_blank"
            rel="noreferrer"
            className="btn-primary"
            style={{ fontSize: 'var(--text-xs)', textDecoration: 'none' }}
          >
            <ExternalLink size={13} /> Open Source PDF
          </a>
        </div>
      </div>
    </div>
  );
};
