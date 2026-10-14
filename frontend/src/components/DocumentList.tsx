'use client';

import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  FileText,
  Trash2,
  ExternalLink,
  BookOpen,
  CheckCircle2,
  Clock,
  AlertCircle,
  FileUp,
} from 'lucide-react';
import { Document, DocumentPage } from '@/types';
import { api } from '@/lib/api';

interface DocumentListProps {
  documents: Document[];
  workspaceId: string;
  onRefresh: () => void;
}

export const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  workspaceId,
  onRefresh,
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [selectedDocPages, setSelectedDocPages] = useState<{ doc: Document; pages: DocumentPage[] } | null>(null);
  const [loadingPages, setLoadingPages] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUploadError('Only PDF documents are supported in this milestone.');
      return;
    }

    if (file.size > 15 * 1024 * 1024) {
      setUploadError('File exceeds 15 MB maximum size limit.');
      return;
    }

    setIsUploading(true);
    setUploadError(null);

    try {
      await api.documents.upload(workspaceId, file);
      onRefresh();
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleDelete = async (docId: string, filename: string) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}"? All chunks and vector indexes will be removed.`)) {
      return;
    }

    try {
      await api.documents.delete(workspaceId, docId);
      onRefresh();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to delete document');
    }
  };

  const handleInspectPages = async (doc: Document) => {
    setLoadingPages(true);
    try {
      const pages = await api.documents.getPages(workspaceId, doc.id);
      setSelectedDocPages({ doc, pages });
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to load document pages');
    } finally {
      setLoadingPages(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Upload Zone (Drag-and-drop & button fallback) */}
      <div
        className="surface-card"
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        style={{
          padding: 'var(--space-8) var(--space-6)',
          textAlign: 'center',
          border: '2px dashed var(--color-border-strong)',
          cursor: 'pointer',
          position: 'relative',
        }}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: 'none' }}
          accept=".pdf,application/pdf"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFileUpload(e.target.files[0]);
            }
          }}
        />

        <div
          style={{
            width: '54px',
            height: '54px',
            borderRadius: 'var(--radius-pill)',
            background: 'var(--color-surface-subtle)',
            border: '1px solid var(--color-border-strong)',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: 'var(--space-3)',
          }}
        >
          {isUploading ? (
            <Clock size={24} color="var(--color-brand)" />
          ) : (
            <UploadCloud size={24} color="var(--color-brand)" />
          )}
        </div>

        <h3 style={{ fontSize: 'var(--text-lg)', fontWeight: 'var(--weight-bold)', marginBottom: 'var(--space-1)' }}>
          {isUploading ? 'Extracting Text & Generating 768-dim Vectors...' : 'Upload Workspace PDF Document'}
        </h3>
        <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', maxWidth: '480px', margin: '0 auto' }}>
          Drag and drop your file here, or click anywhere to select. PyMuPDF extracts page provenance
          and gemini-embedding-2 indexes vector chunks automatically.
        </p>

        <div style={{ marginTop: 'var(--space-4)', display: 'flex', justifyContent: 'center' }}>
          <button
            type="button"
            className="btn-secondary"
            onClick={(e) => {
              e.stopPropagation();
              fileInputRef.current?.click();
            }}
          >
            <FileUp size={14} /> Browse Files
          </button>
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 'var(--space-4)',
            marginTop: 'var(--space-4)',
            fontSize: 'var(--text-xs)',
            color: 'var(--color-text-muted)',
          }}
        >
          <span>• Max 15 MB</span>
          <span>• Embedded text layer</span>
          <span>• Isolated to current workspace</span>
        </div>

        {uploadError && (
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              marginTop: 'var(--space-4)',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 'var(--space-2)',
              padding: 'var(--space-2) var(--space-4)',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--color-danger-soft)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: 'var(--color-danger)',
              fontSize: 'var(--text-xs)',
            }}
          >
            <AlertCircle size={15} />
            <span>{uploadError}</span>
          </div>
        )}
      </div>

      {/* Document Library Section */}
      <div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: 'var(--space-4)',
          }}
        >
          <div>
            <h3 style={{ fontSize: 'var(--text-md)', fontWeight: 'var(--weight-bold)' }}>
              Workspace Documents ({documents.length}/10)
            </h3>
            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
              All documents are isolated to your workspace tenant boundary
            </p>
          </div>

          <button
            onClick={() => fileInputRef.current?.click()}
            className="btn-secondary"
            style={{ fontSize: 'var(--text-xs)' }}
          >
            <FileUp size={13} /> Upload Document
          </button>
        </div>

        {documents.length === 0 ? (
          <div
            className="surface-card"
            style={{
              padding: 'var(--space-10) var(--space-6)',
              textAlign: 'center',
              color: 'var(--color-text-secondary)',
            }}
          >
            <BookOpen size={36} color="var(--color-text-muted)" style={{ marginBottom: 'var(--space-3)' }} />
            <p style={{ fontSize: 'var(--text-md)', fontWeight: 'var(--weight-semibold)' }}>No documents uploaded yet</p>
            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', marginTop: 'var(--space-1)' }}>
              Upload your first PDF report or specification to enable evidence-grounded search and claim verification.
            </p>
          </div>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
              gap: 'var(--space-4)',
            }}
          >
            {documents.map((doc) => {
              const pdfUrl = api.documents.getFileUrl(workspaceId, doc.id);
              return (
                <div
                  key={doc.id}
                  className="surface-card"
                  style={{
                    padding: 'var(--space-4)',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    gap: 'var(--space-4)',
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 'var(--space-2)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                        <div
                          style={{
                            width: '36px',
                            height: '36px',
                            borderRadius: 'var(--radius-xs)',
                            background: 'var(--color-surface-subtle)',
                            border: '1px solid var(--color-border)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                          }}
                        >
                          <FileText size={18} color="var(--color-brand)" />
                        </div>
                        <div style={{ maxWidth: '200px' }}>
                          <h4
                            style={{
                              fontSize: 'var(--text-sm)',
                              fontWeight: 'var(--weight-semibold)',
                              color: 'var(--color-text-primary)',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            }}
                            title={doc.filename}
                          >
                            {doc.filename}
                          </h4>
                          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                            {formatFileSize(doc.file_size)} • {doc.page_count} pages
                          </span>
                        </div>
                      </div>

                      <span
                        style={{
                          fontSize: '11px',
                          fontWeight: 'var(--weight-semibold)',
                          padding: '0.15rem 0.45rem',
                          borderRadius: 'var(--radius-xs)',
                          background:
                            doc.status === 'completed'
                              ? 'var(--color-success-soft)'
                              : doc.status === 'processing'
                              ? 'var(--color-info-soft)'
                              : 'var(--color-danger-soft)',
                          border: `1px solid ${
                            doc.status === 'completed'
                              ? 'rgba(16, 185, 129, 0.3)'
                              : doc.status === 'processing'
                              ? 'rgba(59, 130, 246, 0.3)'
                              : 'rgba(239, 68, 68, 0.3)'
                          }`,
                          color:
                            doc.status === 'completed'
                              ? 'var(--color-success)'
                              : doc.status === 'processing'
                              ? 'var(--color-info)'
                              : 'var(--color-danger)',
                          textTransform: 'uppercase',
                        }}
                      >
                        {doc.status}
                      </span>
                    </div>

                    <div
                      style={{
                        marginTop: 'var(--space-3)',
                        padding: 'var(--space-2) var(--space-3)',
                        background: 'var(--color-surface-subtle)',
                        borderRadius: 'var(--radius-xs)',
                        fontSize: '11px',
                        color: 'var(--color-text-muted)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <span>SHA256: {doc.file_hash ? doc.file_hash.substring(0, 10) + '...' : doc.id.substring(0, 8)}</span>
                      <span>{doc.created_at ? new Date(doc.created_at).toLocaleDateString() : 'Recent'}</span>
                    </div>
                  </div>

                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      borderTop: '1px solid var(--color-border)',
                      paddingTop: 'var(--space-3)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                      <button
                        onClick={() => handleInspectPages(doc)}
                        className="btn-ghost"
                        style={{ fontSize: 'var(--text-xs)', padding: 'var(--space-1) var(--space-2)' }}
                      >
                        <BookOpen size={13} /> Pages
                      </button>
                      <a
                        href={pdfUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="btn-ghost"
                        style={{ fontSize: 'var(--text-xs)', padding: 'var(--space-1) var(--space-2)', textDecoration: 'none' }}
                      >
                        <ExternalLink size={13} /> PDF
                      </a>
                    </div>

                    <button
                      onClick={() => handleDelete(doc.id, doc.filename)}
                      className="btn-ghost"
                      style={{ padding: 'var(--space-1)', color: 'var(--color-danger)' }}
                      title="Delete document"
                      aria-label={`Delete ${doc.filename}`}
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Pages Provenance Inspection Modal */}
      {selectedDocPages && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(10, 14, 23, 0.75)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
            padding: 'var(--space-4)',
          }}
          role="dialog"
          aria-modal="true"
        >
          <div
            className="surface-card animate-entrance"
            style={{
              width: '100%',
              maxWidth: '720px',
              maxHeight: '85vh',
              display: 'flex',
              flexDirection: 'column',
              padding: 'var(--space-5)',
              boxShadow: 'var(--shadow-dialog)',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                paddingBottom: 'var(--space-3)',
                borderBottom: '1px solid var(--color-border)',
              }}
            >
              <div>
                <h3 style={{ fontSize: 'var(--text-md)', fontWeight: 'var(--weight-bold)' }}>
                  Page Provenance: {selectedDocPages.doc.filename}
                </h3>
                <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                  {selectedDocPages.pages.length} total pages extracted via PyMuPDF
                </p>
              </div>
              <button
                onClick={() => setSelectedDocPages(null)}
                className="btn-ghost"
                style={{ padding: 'var(--space-1)' }}
                aria-label="Close modal"
              >
                ✕
              </button>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', padding: 'var(--space-4) 0', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              {selectedDocPages.pages.map((p) => (
                <div
                  key={p.id}
                  className="surface-card-subtle"
                  style={{
                    padding: 'var(--space-4)',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginBottom: 'var(--space-2)',
                      fontSize: 'var(--text-xs)',
                      color: 'var(--color-brand)',
                      fontWeight: 'var(--weight-semibold)',
                    }}
                  >
                    <span>Page {p.page_number}</span>
                    <span style={{ color: 'var(--color-text-muted)' }}>{p.char_count} chars</span>
                  </div>
                  <pre
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 'var(--text-xs)',
                      color: 'var(--color-text-secondary)',
                      whiteSpace: 'pre-wrap',
                      maxHeight: '200px',
                      overflowY: 'auto',
                      lineHeight: 'var(--line-body)',
                    }}
                  >
                    {p.text_content}
                  </pre>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
