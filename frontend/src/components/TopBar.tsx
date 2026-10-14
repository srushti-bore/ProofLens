'use client';

import React, { useState } from 'react';
import {
  Sparkles,
  ChevronDown,
  MoreHorizontal,
  Share2,
  Download,
  UploadCloud,
  Check,
} from 'lucide-react';
import { Workspace, User } from '@/types';
import { api } from '@/lib/api';

interface TopBarProps {
  activeTab: 'qa' | 'documents' | 'claims' | 'comparison' | 'analytics';
  activeWorkspace: Workspace | null;
  workspaces: Workspace[];
  onSelectWorkspace: (ws: Workspace) => void;
  documentCount: number;
  onOpenUpload: () => void;
  currentUser: User | null;
  onOpenAuth: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  activeTab,
  activeWorkspace,
  workspaces,
  onSelectWorkspace,
  documentCount,
  onOpenUpload,
  currentUser,
  onOpenAuth,
}) => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [exporting, setExporting] = useState(false);

  const handleExportReport = async () => {
    if (!activeWorkspace) return;
    setExporting(true);
    try {
      const res = await api.reports.export(activeWorkspace.id);
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

  return (
    <header
      style={{
        height: 'var(--topbar-height)',
        backgroundColor: '#FFFFFF',
        borderBottom: '1px solid #F3F3F6',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        flexShrink: 0,
        position: 'relative',
        zIndex: 20,
      }}
    >
      {/* Left: Model / Workspace Dropdown Pill (Reference: [+] Cortex ∨) */}
      <div style={{ position: 'relative' }}>
        <button
          onClick={() => setIsDropdownOpen(!isDropdownOpen)}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            background: '#FFFFFF',
            border: '1px solid #E4E4E7',
            borderRadius: '999px',
            padding: '6px 14px 6px 8px',
            cursor: 'pointer',
            fontSize: '13px',
            fontWeight: 600,
            color: '#18181B',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)',
            transition: 'all 150ms ease',
          }}
          aria-expanded={isDropdownOpen}
        >
          <div
            style={{
              width: '22px',
              height: '22px',
              borderRadius: '6px',
              background: 'linear-gradient(135deg, #7C3AED 0%, #A855F7 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Sparkles size={12} color="#FFFFFF" />
          </div>
          <span>{activeWorkspace ? activeWorkspace.name : 'ProofLens AI'}</span>
          <ChevronDown size={14} color="#71717A" />
        </button>

        {isDropdownOpen && (
          <div
            className="animate-entrance"
            style={{
              position: 'absolute',
              top: 'calc(100% + 6px)',
              left: 0,
              width: '240px',
              backgroundColor: '#FFFFFF',
              borderRadius: '14px',
              border: '1px solid #E4E4E7',
              boxShadow: '0 10px 30px rgba(0, 0, 0, 0.08)',
              padding: '6px',
              zIndex: 50,
            }}
          >
            <div
              style={{
                fontSize: '11px',
                fontWeight: 600,
                color: '#9CA3AF',
                padding: '6px 10px',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
              }}
            >
              Active Workspace
            </div>
            {workspaces.map((ws) => (
              <button
                key={ws.id}
                onClick={() => {
                  onSelectWorkspace(ws);
                  setIsDropdownOpen(false);
                }}
                style={{
                  width: '100%',
                  padding: '8px 10px',
                  borderRadius: '8px',
                  background: ws.id === activeWorkspace?.id ? '#F5EEFD' : 'transparent',
                  border: 'none',
                  color: ws.id === activeWorkspace?.id ? '#7C3AED' : '#18181B',
                  textAlign: 'left',
                  fontSize: '12px',
                  fontWeight: ws.id === activeWorkspace?.id ? 600 : 500,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <span>{ws.name}</span>
                {ws.id === activeWorkspace?.id && <Check size={14} color="#7C3AED" />}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Right Actions: ... | Link | Export chat | Upgrade / Upload */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {/* More options button */}
        <button
          className="btn-pill"
          style={{ width: '32px', height: '32px', padding: 0, borderRadius: '50%' }}
          title="More options"
        >
          <MoreHorizontal size={15} color="#71717A" />
        </button>

        {/* Share / Link button */}
        <button
          className="btn-pill"
          style={{ width: '32px', height: '32px', padding: 0, borderRadius: '50%' }}
          title="Share workspace"
          onClick={() => {
            navigator.clipboard.writeText(window.location.href);
            alert('Workspace URL copied to clipboard!');
          }}
        >
          <Share2 size={14} color="#71717A" />
        </button>

        {/* Export chat / report pill */}
        <button
          onClick={handleExportReport}
          disabled={exporting || !activeWorkspace}
          className="btn-pill"
          style={{ fontSize: '12px', fontWeight: 600 }}
          title="Export citation-linked investigation report"
        >
          <Download size={13} color="#71717A" />
          <span>{exporting ? 'Exporting...' : 'Export chat'}</span>
        </button>

        {/* Upgrade / + Upload PDF (Solid Black Pill Button) */}
        <button
          onClick={onOpenUpload}
          className="btn-dark"
          style={{
            padding: '7px 16px',
            borderRadius: '999px',
            fontSize: '12px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
          title="Ingest new PDF with PyMuPDF provenance"
        >
          <UploadCloud size={14} />
          <span>+ Upload PDF</span>
        </button>
      </div>
    </header>
  );
};
