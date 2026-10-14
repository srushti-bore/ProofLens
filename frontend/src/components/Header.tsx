'use client';

import React, { useState } from 'react';
import {
  FolderArchive,
  MessageSquareText,
  ShieldCheck,
  GitCompare,
  BarChart3,
  Layers,
  Plus,
  LogIn,
  LogOut,
  Sparkles,
  ChevronDown,
} from 'lucide-react';
import { Workspace, User } from '@/types';

interface HeaderProps {
  activeTab: 'documents' | 'qa' | 'claims' | 'comparison' | 'analytics';
  setActiveTab: (tab: 'documents' | 'qa' | 'claims' | 'comparison' | 'analytics') => void;
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  onSelectWorkspace: (ws: Workspace) => void;
  onCreateWorkspace: () => void;
  currentUser: User | null;
  onOpenAuth: () => void;
  onLogout: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  workspaces,
  activeWorkspace,
  onSelectWorkspace,
  onCreateWorkspace,
  currentUser,
  onOpenAuth,
  onLogout,
}) => {
  const [isWorkspaceMenuOpen, setIsWorkspaceMenuOpen] = useState(false);

  const navItems = [
    { id: 'documents', label: 'Documents', icon: FolderArchive, badge: null },
    { id: 'qa', label: 'Evidence Q&A', icon: MessageSquareText, badge: 'Grounded' },
    { id: 'claims', label: 'Claim Verifier', icon: ShieldCheck, badge: '4-Tier' },
    { id: 'comparison', label: 'Comparison', icon: GitCompare, badge: null },
    { id: 'analytics', label: 'Analytics', icon: BarChart3, badge: null },
  ] as const;

  return (
    <header
      style={{
        borderBottom: '1px solid var(--border-subtle)',
        background: 'rgba(10, 14, 23, 0.85)',
        backdropFilter: 'blur(20px)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
      }}
    >
      <div
        style={{
          maxWidth: '1440px',
          margin: '0 auto',
          padding: '0.85rem 1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1.5rem',
        }}
      >
        {/* Brand Logo & Slogan */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.9rem' }}>
          <div
            style={{
              width: '38px',
              height: '38px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--brand-gradient)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: 'var(--shadow-glow)',
            }}
          >
            <Sparkles size={20} color="#FFFFFF" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span
                style={{
                  fontSize: '1.2rem',
                  fontWeight: 800,
                  letterSpacing: '-0.02em',
                  background: 'linear-gradient(135deg, #FFFFFF 30%, #38BDF8 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                ProofLens AI
              </span>
              <span
                style={{
                  fontSize: '0.65rem',
                  textTransform: 'uppercase',
                  fontWeight: 700,
                  letterSpacing: '0.06em',
                  padding: '0.15rem 0.45rem',
                  borderRadius: 'var(--radius-sm)',
                  background: 'rgba(6, 182, 212, 0.15)',
                  color: 'var(--brand-cyan)',
                  border: '1px solid rgba(6, 182, 212, 0.3)',
                }}
              >
                v0.2 RAG
              </span>
            </div>
            <p style={{ fontSize: '0.72rem', color: 'var(--text-tertiary)', fontWeight: 500 }}>
              From Documents to Verifiable Answers
            </p>
          </div>
        </div>

        {/* Workspace Switcher */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setIsWorkspaceMenuOpen(!isWorkspaceMenuOpen)}
            className="btn-secondary"
            style={{
              padding: '0.45rem 0.85rem',
              fontSize: '0.825rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
            aria-label="Select Workspace"
          >
            <Layers size={15} color="var(--brand-cyan)" />
            <span style={{ maxWidth: '160px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {activeWorkspace ? activeWorkspace.name : 'Select Workspace'}
            </span>
            <ChevronDown size={14} color="var(--text-tertiary)" />
          </button>

          {isWorkspaceMenuOpen && (
            <div
              className="glass-panel-elevated animate-fade-in"
              style={{
                position: 'absolute',
                top: '115%',
                left: 0,
                width: '240px',
                padding: '0.5rem',
                zIndex: 100,
              }}
            >
              <div
                style={{
                  padding: '0.35rem 0.5rem',
                  fontSize: '0.7rem',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  color: 'var(--text-tertiary)',
                  letterSpacing: '0.05em',
                }}
              >
                Workspaces ({workspaces.length})
              </div>
              <div style={{ maxHeight: '180px', overflowY: 'auto' }}>
                {workspaces.map((ws) => (
                  <button
                    key={ws.id}
                    onClick={() => {
                      onSelectWorkspace(ws);
                      setIsWorkspaceMenuOpen(false);
                    }}
                    style={{
                      width: '100%',
                      padding: '0.5rem 0.65rem',
                      borderRadius: 'var(--radius-sm)',
                      background: ws.id === activeWorkspace?.id ? 'rgba(6, 182, 212, 0.12)' : 'transparent',
                      border: ws.id === activeWorkspace?.id ? '1px solid rgba(6, 182, 212, 0.25)' : 'none',
                      color: ws.id === activeWorkspace?.id ? 'var(--brand-cyan)' : 'var(--text-primary)',
                      textAlign: 'left',
                      fontSize: '0.825rem',
                      fontWeight: ws.id === activeWorkspace?.id ? 600 : 400,
                      cursor: 'pointer',
                      display: 'block',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {ws.name}
                  </button>
                ))}
              </div>
              <div style={{ borderTop: '1px solid var(--border-subtle)', marginTop: '0.4rem', paddingTop: '0.4rem' }}>
                <button
                  onClick={() => {
                    setIsWorkspaceMenuOpen(false);
                    onCreateWorkspace();
                  }}
                  className="btn-ghost"
                  style={{ width: '100%', justifyContent: 'flex-start', fontSize: '0.8rem', color: 'var(--brand-cyan)' }}
                >
                  <Plus size={14} /> Create Workspace
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Center Navigation Tabs */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                style={{
                  background: isActive ? 'rgba(255, 255, 255, 0.08)' : 'transparent',
                  border: isActive ? '1px solid var(--border-medium)' : '1px solid transparent',
                  color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                  padding: '0.5rem 0.95rem',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.85rem',
                  fontWeight: isActive ? 600 : 500,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  transition: 'all 0.18s ease',
                  position: 'relative',
                }}
              >
                <Icon size={16} color={isActive ? 'var(--brand-cyan)' : 'var(--text-tertiary)'} />
                <span>{item.label}</span>
                {item.badge && (
                  <span
                    style={{
                      fontSize: '0.625rem',
                      padding: '0.1rem 0.35rem',
                      borderRadius: 'var(--radius-sm)',
                      background: 'rgba(6, 182, 212, 0.15)',
                      color: 'var(--brand-cyan)',
                      fontWeight: 700,
                    }}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* User Account / Auth Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {currentUser ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div
                style={{
                  fontSize: '0.8rem',
                  padding: '0.35rem 0.75rem',
                  borderRadius: 'var(--radius-md)',
                  background: 'rgba(255, 255, 255, 0.04)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-secondary)',
                }}
              >
                {currentUser.email}
              </div>
              <button
                onClick={onLogout}
                className="btn-ghost"
                style={{ padding: '0.4rem', color: 'var(--status-contradicted-text)' }}
                title="Log out"
                aria-label="Log out"
              >
                <LogOut size={16} />
              </button>
            </div>
          ) : (
            <button onClick={onOpenAuth} className="btn-primary" style={{ padding: '0.45rem 1rem', fontSize: '0.825rem' }}>
              <LogIn size={15} /> Sign In / Register
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
