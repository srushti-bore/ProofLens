'use client';

import React, { useState } from 'react';
import { X, Layers, Plus } from 'lucide-react';
import { api } from '@/lib/api';
import { Workspace } from '@/types';

interface CreateWorkspaceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onWorkspaceCreated: (workspace: Workspace) => void;
}

export const CreateWorkspaceModal: React.FC<CreateWorkspaceModalProps> = ({
  isOpen,
  onClose,
  onWorkspaceCreated,
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || loading) return;

    setLoading(true);
    setError(null);

    try {
      const ws = await api.workspaces.create(name.trim(), description.trim() || undefined);
      onWorkspaceCreated(ws);
      setName('');
      setDescription('');
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create workspace');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(17, 24, 39, 0.45)',
        backdropFilter: 'blur(8px)',
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
          maxWidth: '420px',
          padding: 'var(--space-6)',
          position: 'relative',
          boxShadow: 'var(--shadow-dialog)',
        }}
      >
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: 'var(--space-4)',
            right: 'var(--space-4)',
            background: 'transparent',
            border: 'none',
            color: 'var(--color-text-muted)',
            cursor: 'pointer',
          }}
          aria-label="Close dialog"
        >
          <X size={18} />
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: 'var(--radius-xs)',
              background: 'var(--color-accent-soft)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Layers size={18} color="var(--color-brand)" />
          </div>
          <div>
            <h3 style={{ fontSize: 'var(--text-md)', fontWeight: 'var(--weight-bold)' }}>New Workspace</h3>
            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
              Creates an isolated tenant boundary for documents and vector search.
            </p>
          </div>
        </div>

        {error && (
          <div
            style={{
              background: 'var(--color-danger-soft)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: 'var(--color-danger)',
              padding: 'var(--space-3)',
              borderRadius: 'var(--radius-sm)',
              fontSize: 'var(--text-xs)',
              marginBottom: 'var(--space-3)',
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <div>
            <label style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', display: 'block', marginBottom: 'var(--space-1)' }}>
              Workspace Name
            </label>
            <input
              type="text"
              className="input-field"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Legal Contract Review"
              required
            />
          </div>

          <div>
            <label style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', display: 'block', marginBottom: 'var(--space-1)' }}>
              Description (Optional)
            </label>
            <textarea
              className="input-field"
              rows={2}
              style={{ resize: 'none' }}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief summary of investigations in this workspace..."
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-2)', marginTop: 'var(--space-2)' }}>
            <button type="button" onClick={onClose} className="btn-secondary" style={{ fontSize: 'var(--text-xs)' }}>
              Cancel
            </button>
            <button type="submit" disabled={loading || !name.trim()} className="btn-primary" style={{ fontSize: 'var(--text-xs)' }}>
              <Plus size={13} /> {loading ? 'Creating...' : 'Create Workspace'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
