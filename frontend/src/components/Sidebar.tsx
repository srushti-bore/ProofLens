'use client';

import React, { useState } from 'react';
import {
  Compass,
  FolderOpen,
  BookOpen,
  Clock,
  Plus,
  Search,
  LogOut,
  PanelLeftClose,
  PanelLeft,
  ChevronDown,
  Layers,
  Sparkles,
} from 'lucide-react';
import { Workspace, User } from '@/types';

interface SidebarProps {
  activeTab: 'qa' | 'documents' | 'claims' | 'comparison' | 'analytics';
  setActiveTab: (tab: 'qa' | 'documents' | 'claims' | 'comparison' | 'analytics') => void;
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  onSelectWorkspace: (ws: Workspace) => void;
  onCreateWorkspace: () => void;
  currentUser: User | null;
  onOpenAuth: () => void;
  onLogout: () => void;
  documentCount: number;
  onNewChat?: () => void;
  onSelectPrompt?: (prompt: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  workspaces,
  activeWorkspace,
  onSelectWorkspace,
  onCreateWorkspace,
  currentUser,
  onOpenAuth,
  onLogout,
  documentCount,
  onNewChat,
  onSelectPrompt,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isWorkspaceMenuOpen, setIsWorkspaceMenuOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  // Grouped Chat History (matching Dribbble reference)
  const historyBuckets = [
    {
      label: 'Today',
      items: [
        'Analyze Europa ice crust thickness findings',
        'ProofLens AI 768-dim vector embedding spec',
        'Verify 4-tier truth status on Voyager 1 launch',
      ],
    },
    {
      label: 'Yesterday',
      items: [
        'Summarize cross-document comparison matrix',
        'Evaluate PyMuPDF page-level extraction bounds',
      ],
    },
    {
      label: '7 days',
      items: [
        'Check evidence grounding and citation validity',
        'Audit tenant isolation on multi-user workspaces',
        'Export Markdown investigation report with citations',
        'Examine explicit abstention on out-of-scope query',
      ],
    },
  ];

  const filteredBuckets = searchQuery.trim()
    ? historyBuckets
        .map((b) => ({
          ...b,
          items: b.items.filter((item) =>
            item.toLowerCase().includes(searchQuery.toLowerCase())
          ),
        }))
        .filter((b) => b.items.length > 0)
    : historyBuckets;

  const navItems = [
    {
      id: 'qa' as const,
      label: 'Explore',
      icon: Compass,
      badge: null,
    },
    {
      id: 'comparison' as const,
      label: 'Library',
      icon: BookOpen,
      badge: null,
    },
    {
      id: 'documents' as const,
      label: 'Files',
      icon: FolderOpen,
      badge: documentCount > 0 ? `${documentCount}` : null,
    },
    {
      id: 'analytics' as const,
      label: 'History',
      icon: Clock,
      badge: null,
    },
  ];

  return (
    <aside
      style={{
        width: collapsed ? '72px' : 'var(--sidebar-width)',
        backgroundColor: '#F8F8FA',
        borderRight: '1px solid #ECECF1',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        flexShrink: 0,
        transition: 'width 240ms cubic-bezier(0.2, 0, 0, 1)',
        position: 'relative',
        userSelect: 'none',
      }}
      aria-label="Main Navigation"
    >
      {/* 1. Header with Logo & Collapse Toggle */}
      <div
        style={{
          padding: '18px 16px 14px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'space-between',
          borderBottom: '1px solid #F1F1F4',
        }}
      >
        {!collapsed && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #7C3AED 0%, #A855F7 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 10px rgba(124, 58, 237, 0.25)',
              }}
            >
              <Sparkles size={15} color="#FFFFFF" />
            </div>
            <span
              style={{
                fontSize: '16px',
                fontWeight: 700,
                color: '#18181B',
                letterSpacing: '-0.02em',
              }}
            >
              ProofLens
            </span>
          </div>
        )}

        <button
          onClick={() => setCollapsed(!collapsed)}
          style={{
            background: 'transparent',
            border: 'none',
            color: '#71717A',
            cursor: 'pointer',
            padding: '4px',
            borderRadius: '6px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'color 150ms ease',
          }}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <PanelLeft size={18} /> : <PanelLeftClose size={18} />}
        </button>
      </div>

      {!collapsed ? (
        <>
          {/* 2. "+ New chat" Button */}
          <div style={{ padding: '14px 16px 8px' }}>
            <button
              onClick={() => {
                setActiveTab('qa');
                if (onNewChat) onNewChat();
              }}
              className="btn-dark"
              style={{
                width: '100%',
                padding: '10px 14px',
                borderRadius: '12px',
                fontSize: '13px',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
              }}
            >
              <Plus size={16} /> New chat
            </button>
          </div>

          {/* 3. Search Bar */}
          <div style={{ padding: '6px 16px 12px' }}>
            <div className="sidebar-search-box">
              <Search size={14} color="#9CA3AF" />
              <input
                type="text"
                placeholder="Search..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="sidebar-search-input"
              />
              <span
                style={{
                  fontSize: '10px',
                  color: '#A1A1AA',
                  border: '1px solid #E4E4E7',
                  borderRadius: '4px',
                  padding: '1px 4px',
                  background: '#FFFFFF',
                }}
              >
                ⌘K
              </span>
            </div>
          </div>

          {/* 4. Navigation Menu Items */}
          <div style={{ padding: '0 12px 10px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: '10px',
                    background: isActive ? '#FFFFFF' : 'transparent',
                    border: 'none',
                    boxShadow: isActive ? '0 1px 3px rgba(0, 0, 0, 0.05)' : 'none',
                    color: isActive ? '#111827' : '#6B7280',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    transition: 'all 150ms ease',
                    textAlign: 'left',
                    fontWeight: isActive ? 600 : 500,
                    fontSize: '13px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Icon size={16} color={isActive ? '#7C3AED' : '#9CA3AF'} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span
                      style={{
                        fontSize: '11px',
                        fontWeight: 600,
                        padding: '1px 6px',
                        borderRadius: '10px',
                        background: '#EDE9FE',
                        color: '#7C3AED',
                      }}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* 5. Chat History Buckets List */}
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: '8px 12px',
              display: 'flex',
              flexDirection: 'column',
              gap: '14px',
            }}
          >
            {filteredBuckets.map((bucket, bIdx) => (
              <div key={bIdx}>
                <div
                  style={{
                    fontSize: '11px',
                    fontWeight: 600,
                    color: '#9CA3AF',
                    padding: '0 8px 6px',
                    letterSpacing: '0.02em',
                  }}
                >
                  {bucket.label}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                  {bucket.items.map((item, itemIdx) => (
                    <button
                      key={itemIdx}
                      onClick={() => {
                        setActiveTab('qa');
                        if (onSelectPrompt) onSelectPrompt(item);
                      }}
                      style={{
                        width: '100%',
                        padding: '7px 8px',
                        borderRadius: '8px',
                        background: 'transparent',
                        border: 'none',
                        color: '#4B5563',
                        fontSize: '12px',
                        textAlign: 'left',
                        cursor: 'pointer',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        display: 'block',
                        transition: 'all 120ms ease',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = '#FFFFFF';
                        e.currentTarget.style.color = '#111827';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = 'transparent';
                        e.currentTarget.style.color = '#4B5563';
                      }}
                      title={item}
                    >
                      {item}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* 6. Bottom User Profile Card */}
          <div
            style={{
              padding: '12px 14px',
              borderTop: '1px solid #ECECF1',
              background: '#F8F8FA',
            }}
          >
            {currentUser ? (
              <div>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '8px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
                    {/* User Avatar */}
                    <div
                      style={{
                        width: '32px',
                        height: '32px',
                        borderRadius: '50%',
                        background: 'linear-gradient(135deg, #A855F7 0%, #EC4899 100%)',
                        color: '#FFFFFF',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '12px',
                        fontWeight: 700,
                        flexShrink: 0,
                      }}
                    >
                      {currentUser.full_name
                        ? currentUser.full_name.slice(0, 2).toUpperCase()
                        : currentUser.email.slice(0, 2).toUpperCase()}
                    </div>
                    <div style={{ minWidth: 0 }}>
                      <span
                        style={{
                          fontSize: '12px',
                          fontWeight: 600,
                          color: '#18181B',
                          display: 'block',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        }}
                      >
                        {currentUser.full_name || 'Jackson Vance'}
                      </span>
                      <span
                        style={{
                          fontSize: '11px',
                          color: '#71717A',
                          display: 'block',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        }}
                      >
                        {currentUser.email}
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={onLogout}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: '#A1A1AA',
                      cursor: 'pointer',
                      padding: '4px',
                      borderRadius: '6px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      transition: 'color 120ms ease',
                    }}
                    title="Sign Out"
                  >
                    <LogOut size={15} />
                  </button>
                </div>

                {/* Evidence Quota Progress Bar (Pink to Purple gradient) */}
                <div
                  style={{
                    width: '100%',
                    height: '4px',
                    borderRadius: '999px',
                    background: '#E4E4E7',
                    overflow: 'hidden',
                  }}
                  title="Evidence Storage: 68% utilized"
                >
                  <div
                    style={{
                      width: '68%',
                      height: '100%',
                      borderRadius: '999px',
                      background: 'linear-gradient(90deg, #EC4899 0%, #8B5CF6 100%)',
                    }}
                  />
                </div>
              </div>
            ) : (
              <button
                onClick={onOpenAuth}
                className="btn-dark"
                style={{ width: '100%', padding: '8px 12px', fontSize: '12px' }}
              >
                Sign In / Register
              </button>
            )}
          </div>
        </>
      ) : (
        /* Collapsed Sidebar View */
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            padding: '16px 0',
            gap: '16px',
            flex: 1,
          }}
        >
          <button
            onClick={() => {
              setActiveTab('qa');
              if (onNewChat) onNewChat();
            }}
            className="btn-dark"
            style={{ width: '40px', height: '40px', borderRadius: '12px', padding: 0 }}
            title="New Chat"
          >
            <Plus size={18} />
          </button>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '12px' }}>
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '10px',
                    background: isActive ? '#FFFFFF' : 'transparent',
                    border: 'none',
                    boxShadow: isActive ? '0 1px 3px rgba(0, 0, 0, 0.05)' : 'none',
                    color: isActive ? '#7C3AED' : '#71717A',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                  }}
                  title={item.label}
                >
                  <Icon size={18} />
                </button>
              );
            })}
          </div>
        </div>
      )}
    </aside>
  );
};
