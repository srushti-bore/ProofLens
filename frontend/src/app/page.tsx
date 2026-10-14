'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { Sidebar } from '@/components/Sidebar';
import { TopBar } from '@/components/TopBar';
import { AuthModal } from '@/components/AuthModal';
import { CreateWorkspaceModal } from '@/components/CreateWorkspaceModal';
import { DocumentList } from '@/components/DocumentList';
import { QAPanel } from '@/components/QAPanel';
import { ClaimVerificationPanel } from '@/components/ClaimVerificationPanel';
import { DocumentComparisonPanel } from '@/components/DocumentComparisonPanel';
import { AnalyticsPanel } from '@/components/AnalyticsPanel';
import { CitationDrawer } from '@/components/CitationDrawer';
import { Citation, Document, User, Workspace } from '@/types';
import { api } from '@/lib/api';

export default function Home() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeWorkspace, setActiveWorkspace] = useState<Workspace | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [activeTab, setActiveTab] = useState<'qa' | 'documents' | 'claims' | 'comparison' | 'analytics'>('qa');
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const [initialPrompt, setInitialPrompt] = useState<string | undefined>(undefined);

  // Modals
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [isCreateWsOpen, setIsCreateWsOpen] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);

  // Load documents for active workspace
  const refreshDocuments = useCallback(async () => {
    if (!activeWorkspace) return;
    try {
      const docs = await api.documents.list(activeWorkspace.id);
      setDocuments(docs);
    } catch (err) {
      console.error('Failed to load workspace documents:', err);
    }
  }, [activeWorkspace]);

  // Load workspaces
  const refreshWorkspaces = useCallback(async () => {
    try {
      const list = await api.workspaces.list();
      setWorkspaces(list);
      if (list.length > 0) {
        setActiveWorkspace((prev) => {
          if (!prev) return list[0];
          const found = list.find((w) => w.id === prev.id);
          return found || list[0];
        });
      } else {
        try {
          const defaultWs = await api.workspaces.create(
            'Primary Investigation Workspace',
            'Default workspace for evidence analysis'
          );
          setWorkspaces([defaultWs]);
          setActiveWorkspace(defaultWs);
        } catch (e) {
          console.error('Failed to create default workspace:', e);
        }
      }
    } catch (err) {
      console.error('Failed to load workspaces:', err);
    }
  }, []);

  // Initialize Session
  useEffect(() => {
    const initSession = async () => {
      setInitialLoading(true);
      const token = api.getToken();

      let activeUser: User | null = null;
      if (token) {
        try {
          activeUser = await api.auth.getMe();
          setCurrentUser(activeUser);
          await refreshWorkspaces();
        } catch {
          api.clearToken();
          setCurrentUser(null);
          activeUser = null;
        }
      }

      if (!activeUser) {
        // Auto-demo account login for immediate seamless demonstration
        try {
          let tokenRes;
          try {
            tokenRes = await api.auth.login('demo@prooflens.ai', 'DemoSecure123!');
          } catch {
            try {
              tokenRes = await api.auth.register('demo@prooflens.ai', 'DemoSecure123!', 'Dr. Evelyn Vance');
            } catch {
              tokenRes = await api.auth.login('demo@prooflens.ai', 'DemoSecure123!');
            }
          }
          if (tokenRes?.access_token) {
            api.setToken(tokenRes.access_token);
            const user = await api.auth.getMe();
            setCurrentUser(user);
            await refreshWorkspaces();
          }
        } catch (demoErr) {
          console.warn('Demo auto-login skipped; awaiting manual login:', demoErr);
        }
      }
      setInitialLoading(false);
    };

    initSession();
  }, [refreshWorkspaces]);

  // Refresh documents whenever active workspace changes
  useEffect(() => {
    if (activeWorkspace) {
      refreshDocuments();
    } else {
      setDocuments([]);
    }
  }, [activeWorkspace, refreshDocuments]);

  const handleLogout = () => {
    api.clearToken();
    setCurrentUser(null);
    setWorkspaces([]);
    setActiveWorkspace(null);
    setDocuments([]);
    setIsAuthOpen(true);
  };

  const handleAuthSuccess = async (user: User) => {
    setCurrentUser(user);
    await refreshWorkspaces();
  };

  const handleWorkspaceCreated = (ws: Workspace) => {
    setWorkspaces((prev) => [ws, ...prev]);
    setActiveWorkspace(ws);
  };

  const getUserFirstName = () => {
    if (currentUser?.full_name) {
      return currentUser.full_name.split(' ')[0];
    }
    return 'Jackson';
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px',
        background: 'var(--color-canvas-gradient)',
      }}
    >
      {/* Floating Centered Card Container (Reference: Dribbble "Cortex" Layout) */}
      <div className="app-shell-floating">
        {/* Left Sidebar Navigation */}
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          workspaces={workspaces}
          activeWorkspace={activeWorkspace}
          onSelectWorkspace={(ws) => setActiveWorkspace(ws)}
          onCreateWorkspace={() => setIsCreateWsOpen(true)}
          currentUser={currentUser}
          onOpenAuth={() => setIsAuthOpen(true)}
          onLogout={handleLogout}
          documentCount={documents.length}
          onNewChat={() => {
            setActiveTab('qa');
            setInitialPrompt(undefined);
          }}
          onSelectPrompt={(p) => {
            setActiveTab('qa');
            setInitialPrompt(p);
          }}
        />

        {/* Right Content Area */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', minWidth: 0, overflow: 'hidden' }}>
          {/* TopBar Header */}
          <TopBar
            activeTab={activeTab}
            activeWorkspace={activeWorkspace}
            workspaces={workspaces}
            onSelectWorkspace={(ws) => setActiveWorkspace(ws)}
            documentCount={documents.length}
            onOpenUpload={() => setActiveTab('documents')}
            currentUser={currentUser}
            onOpenAuth={() => setIsAuthOpen(true)}
          />

          {/* View Content */}
          <main
            style={{
              flex: 1,
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              background: '#FFFFFF',
            }}
          >
            {initialLoading ? (
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px' }}>
                <div
                  style={{
                    width: '38px',
                    height: '38px',
                    borderRadius: '50%',
                    border: '3px solid #EDE9FE',
                    borderTopColor: '#7C3AED',
                    animation: 'spin 1s linear infinite',
                    marginBottom: '16px',
                  }}
                />
                <p style={{ fontSize: '14px', fontWeight: 600, color: '#111827' }}>
                  Connecting to ProofLens AI Engine...
                </p>
                <p style={{ fontSize: '12px', color: '#6B7280', marginTop: '4px' }}>
                  Verifying tenant isolation and workspace credentials
                </p>
              </div>
            ) : !activeWorkspace ? (
              <div
                style={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '40px',
                  textAlign: 'center',
                }}
              >
                <div
                  className="surface-card"
                  style={{
                    padding: '36px',
                    maxWidth: '460px',
                    textAlign: 'center',
                  }}
                >
                  <h2 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '8px', color: '#111827' }}>
                    No Active Workspace Selected
                  </h2>
                  <p style={{ fontSize: '13px', color: '#6B7280', marginBottom: '20px' }}>
                    Create an isolated investigation workspace to begin uploading documents and verifying claims.
                  </p>
                  <button onClick={() => setIsCreateWsOpen(true)} className="btn-dark">
                    + Create Workspace
                  </button>
                </div>
              </div>
            ) : (
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%' }}>
                {activeTab === 'qa' && (
                  <QAPanel
                    documents={documents}
                    workspaceId={activeWorkspace.id}
                    onOpenCitation={(c) => setActiveCitation(c)}
                    onRefreshDocuments={refreshDocuments}
                    userName={getUserFirstName()}
                    onSwitchTab={(t) => setActiveTab(t)}
                  />
                )}

                {activeTab === 'documents' && (
                  <div style={{ padding: '24px', overflowY: 'auto', flex: 1 }}>
                    <DocumentList
                      documents={documents}
                      workspaceId={activeWorkspace.id}
                      onRefresh={refreshDocuments}
                    />
                  </div>
                )}

                {activeTab === 'claims' && (
                  <div style={{ padding: '24px', overflowY: 'auto', flex: 1 }}>
                    <ClaimVerificationPanel
                      documents={documents}
                      workspaceId={activeWorkspace.id}
                      onOpenCitation={(c) => setActiveCitation(c)}
                    />
                  </div>
                )}

                {activeTab === 'comparison' && (
                  <div style={{ padding: '24px', overflowY: 'auto', flex: 1 }}>
                    <DocumentComparisonPanel
                      documents={documents}
                      workspaceId={activeWorkspace.id}
                    />
                  </div>
                )}

                {activeTab === 'analytics' && (
                  <div style={{ padding: '24px', overflowY: 'auto', flex: 1 }}>
                    <AnalyticsPanel workspaceId={activeWorkspace.id} />
                  </div>
                )}
              </div>
            )}
          </main>
        </div>

        {/* Slide-over Source Inspection Drawer */}
        <CitationDrawer
          isOpen={Boolean(activeCitation)}
          onClose={() => setActiveCitation(null)}
          citation={activeCitation}
          workspaceId={activeWorkspace?.id || ''}
        />

        {/* Auth Modal */}
        <AuthModal
          isOpen={isAuthOpen}
          onClose={() => setIsAuthOpen(false)}
          onAuthSuccess={handleAuthSuccess}
        />

        {/* Create Workspace Modal */}
        <CreateWorkspaceModal
          isOpen={isCreateWsOpen}
          onClose={() => setIsCreateWsOpen(false)}
          onWorkspaceCreated={handleWorkspaceCreated}
        />
      </div>
    </div>
  );
}
