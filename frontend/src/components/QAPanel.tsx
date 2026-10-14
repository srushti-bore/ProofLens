'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  ArrowUp,
  Atom,
  Sparkles,
  SlidersHorizontal,
  Mic,
  Globe,
  Paperclip,
  FileText,
  Lightbulb,
  CheckCircle2,
  Compass,
  AlertTriangle,
  RotateCcw,
  Check,
  HelpCircle,
  ShieldCheck,
} from 'lucide-react';
import { Citation, Document, QAAnswer } from '@/types';
import { api } from '@/lib/api';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  content: string;
  timestamp: string;
  qaData?: QAAnswer;
}

interface QAPanelProps {
  documents: Document[];
  workspaceId: string;
  onOpenCitation: (citation: Citation) => void;
  onRefreshDocuments?: () => void;
  userName?: string;
  onSwitchTab?: (tab: 'qa' | 'documents' | 'claims' | 'comparison' | 'analytics') => void;
}

export const QAPanel: React.FC<QAPanelProps> = ({
  documents,
  workspaceId,
  onOpenCitation,
  onRefreshDocuments,
  userName = 'Jackson',
  onSwitchTab,
}) => {
  const [query, setQuery] = useState('');
  const [deeperResearch, setDeeperResearch] = useState(true);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [showFilterDropdown, setShowFilterDropdown] = useState(false);
  const [showSavedPrompts, setShowSavedPrompts] = useState(false);
  const [loading, setLoading] = useState(false);
  const [uploadingDoc, setUploadingDoc] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Messages stream (empty initially so user sees the Dribbble Welcome Hero)
  const [messages, setMessages] = useState<Message[]>([]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const savedPrompts = [
    'What embedding model and vector dimension does ProofLens AI use?',
    'What is the primary backend framework and database engine?',
    'How does ProofLens enforce workspace tenant data isolation?',
    'What happens when retrieved document evidence is insufficient?',
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (messages.length > 0) {
      scrollToBottom();
    }
  }, [messages, loading]);

  const handleSend = async (queryText?: string) => {
    const textToSend = (queryText || query).trim();
    if (!textToSend || loading) return;

    // 1. Append User Message
    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: 'user',
      content: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setQuery('');
    setLoading(true);
    setError(null);
    setShowSavedPrompts(false);

    try {
      // 2. Execute Grounded QA API Call
      const res = await api.qa.ask(
        workspaceId,
        textToSend,
        selectedDocIds.length > 0 ? selectedDocIds : undefined
      );

      // 3. Append Assistant Grounded Response
      const assistantMsg: Message = {
        id: `assistant-${Date.now()}`,
        sender: 'assistant',
        content: res.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        qaData: res,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: unknown) {
      const errorText = err instanceof Error ? err.message : 'Failed to query workspace';
      setError(errorText);
      const errorMsg: Message = {
        id: `error-${Date.now()}`,
        sender: 'assistant',
        content: `Unable to complete query: ${errorText}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingDoc(true);
    try {
      await api.documents.upload(workspaceId, file);
      if (onRefreshDocuments) onRefreshDocuments();
      alert(`Document "${file.name}" uploaded & parsed with page provenance!`);
    } catch (err: unknown) {
      alert(`Upload failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setUploadingDoc(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const isConversationActive = messages.length > 0;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        minHeight: '100%',
        position: 'relative',
        background: '#FFFFFF',
      }}
    >
      {/* Hidden File Input for "Attach file" */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileUpload}
        accept=".pdf"
        style={{ display: 'none' }}
      />

      {/* VIEW A: EMPTY / HERO STATE (Exact Dribbble Reference Shot) */}
      {!isConversationActive ? (
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            padding: '32px 24px 20px',
            maxWidth: '760px',
            margin: '0 auto',
            width: '100%',
          }}
        >
          {/* 1. 3D Iridescent Lavender Fluid Orb */}
          <div className="orb-container">
            <div className="orb-3d-fluid" />
            <div className="orb-shadow" />
          </div>

          {/* 2. Greeting Header */}
          <div style={{ textAlign: 'center', marginBottom: '24px' }}>
            <div
              style={{
                fontSize: '20px',
                fontWeight: 600,
                color: '#8B5CF6',
                marginBottom: '4px',
                letterSpacing: '-0.01em',
              }}
            >
              Hello, {userName}
            </div>
            <h1
              style={{
                fontSize: '34px',
                fontWeight: 700,
                color: '#111827',
                letterSpacing: '-0.025em',
                lineHeight: 1.2,
              }}
            >
              How can I assist you today?
            </h1>
          </div>

          {/* 3. The Prompt Box Card */}
          <div style={{ width: '100%', marginBottom: '14px' }}>
            <div className="prompt-box-card" style={{ padding: '16px 18px 12px' }}>
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Ask me anything..."
                rows={2}
                style={{
                  width: '100%',
                  border: 'none',
                  outline: 'none',
                  resize: 'none',
                  fontSize: '15px',
                  fontFamily: 'var(--font-sans)',
                  color: '#111827',
                  lineHeight: '1.5',
                  background: 'transparent',
                }}
              />

              {/* Bottom Action Bar inside Prompt Card */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  paddingTop: '8px',
                }}
              >
                {/* Left Controls: Deeper Research, Sparkles, Filter */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <button
                    type="button"
                    onClick={() => setDeeperResearch(!deeperResearch)}
                    className={`deeper-research-pill ${deeperResearch ? 'active' : ''}`}
                    title="Toggle Deep Verification Mode"
                  >
                    <Atom size={14} />
                    <span>Deeper Research</span>
                  </button>

                  <button
                    type="button"
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: '#9CA3AF',
                      cursor: 'pointer',
                      padding: '4px',
                      borderRadius: '6px',
                      display: 'flex',
                      alignItems: 'center',
                    }}
                    title="AI Mode settings"
                  >
                    <Sparkles size={16} />
                  </button>

                  <div style={{ position: 'relative' }}>
                    <button
                      type="button"
                      onClick={() => setShowFilterDropdown(!showFilterDropdown)}
                      style={{
                        background: selectedDocIds.length > 0 ? '#EDE9FE' : 'transparent',
                        border: 'none',
                        color: selectedDocIds.length > 0 ? '#7C3AED' : '#9CA3AF',
                        cursor: 'pointer',
                        padding: '4px',
                        borderRadius: '6px',
                        display: 'flex',
                        alignItems: 'center',
                      }}
                      title="Filter source documents"
                    >
                      <SlidersHorizontal size={16} />
                    </button>

                    {showFilterDropdown && (
                      <div
                        className="surface-card animate-entrance"
                        style={{
                          position: 'absolute',
                          bottom: 'calc(100% + 8px)',
                          left: 0,
                          width: '240px',
                          padding: '10px',
                          zIndex: 60,
                          boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
                          background: '#FFFFFF',
                        }}
                      >
                        <div style={{ fontSize: '11px', fontWeight: 600, color: '#6B7280', marginBottom: '6px' }}>
                          Filter Documents ({documents.length})
                        </div>
                        {documents.length === 0 ? (
                          <div style={{ fontSize: '11px', color: '#9CA3AF' }}>No documents uploaded</div>
                        ) : (
                          documents.map((doc) => {
                            const isSelected = selectedDocIds.includes(doc.id);
                            return (
                              <button
                                key={doc.id}
                                onClick={() => {
                                  setSelectedDocIds((prev) =>
                                    isSelected ? prev.filter((id) => id !== doc.id) : [...prev, doc.id]
                                  );
                                }}
                                style={{
                                  width: '100%',
                                  padding: '6px 8px',
                                  fontSize: '11px',
                                  textAlign: 'left',
                                  borderRadius: '6px',
                                  background: isSelected ? '#F5EEFD' : 'transparent',
                                  color: isSelected ? '#7C3AED' : '#374151',
                                  border: 'none',
                                  cursor: 'pointer',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'space-between',
                                }}
                              >
                                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                  {doc.filename}
                                </span>
                                {isSelected && <Check size={12} />}
                              </button>
                            );
                          })
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* Right Controls: Mic, Globe, Send */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <button
                    type="button"
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: '#9CA3AF',
                      cursor: 'pointer',
                      padding: '4px',
                    }}
                    title="Voice input"
                  >
                    <Mic size={16} />
                  </button>

                  <button
                    type="button"
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: '#9CA3AF',
                      cursor: 'pointer',
                      padding: '4px',
                    }}
                    title="Verify citations"
                  >
                    <Globe size={16} />
                  </button>

                  <button
                    type="button"
                    onClick={() => handleSend()}
                    disabled={!query.trim() || loading}
                    className="btn-send-circle"
                    title="Send message"
                  >
                    <ArrowUp size={16} />
                  </button>
                </div>
              </div>
            </div>

            {/* Prompt Footer Pill Buttons: + Saved prompts | 📎 Attach file */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginTop: '10px',
                padding: '0 4px',
              }}
            >
              <button
                type="button"
                onClick={() => setShowSavedPrompts(!showSavedPrompts)}
                className="btn-pill"
                style={{ fontSize: '11px', padding: '5px 12px', background: '#F8F8FA' }}
              >
                <span>+ Saved prompts</span>
              </button>

              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploadingDoc}
                className="btn-pill"
                style={{ fontSize: '11px', padding: '5px 12px', background: '#F8F8FA' }}
              >
                <Paperclip size={12} color="#71717A" />
                <span>{uploadingDoc ? 'Uploading PDF...' : 'Attach file'}</span>
              </button>
            </div>

            {/* Saved Prompts Expandable Tray */}
            {showSavedPrompts && (
              <div
                className="animate-entrance"
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '8px',
                  marginTop: '12px',
                  padding: '12px',
                  background: '#F9F9FB',
                  borderRadius: '14px',
                  border: '1px solid #EEEEF2',
                }}
              >
                {savedPrompts.map((p, pIdx) => (
                  <button
                    key={pIdx}
                    onClick={() => handleSend(p)}
                    className="suggestion-chip"
                    style={{ fontSize: '11px' }}
                  >
                    {p}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* 4. Three Suggestion Action Cards (Horizontal Grid) */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '14px',
              width: '100%',
              marginTop: '12px',
            }}
          >
            {/* Card 1: Synthesize Data */}
            <div
              className="action-card-suggest"
              onClick={() => handleSend('Synthesize the key factual findings and architectural specifications from the uploaded documents.')}
            >
              <div
                style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '8px',
                  background: '#F3E8FF',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '4px',
                }}
              >
                <FileText size={15} color="#7C3AED" />
              </div>
              <h4 style={{ fontSize: '13px', fontWeight: 700, color: '#111827' }}>
                Synthesize Data
              </h4>
              <p style={{ fontSize: '11px', color: '#6B7280', lineHeight: 1.4 }}>
                Turn raw documents into grounded answers with exact page citations.
              </p>
            </div>

            {/* Card 2: Creative Brainstorm / Verify Claims */}
            <div
              className="action-card-suggest"
              onClick={() => {
                if (onSwitchTab) onSwitchTab('claims');
                else handleSend('Verify claims against the uploaded documents using 4-tier truth taxonomy.');
              }}
            >
              <div
                style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '8px',
                  background: '#FEF3C7',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '4px',
                }}
              >
                <Lightbulb size={15} color="#D97706" />
              </div>
              <h4 style={{ fontSize: '13px', fontWeight: 700, color: '#111827' }}>
                Creative Brainstorm
              </h4>
              <p style={{ fontSize: '11px', color: '#6B7280', lineHeight: 1.4 }}>
                Evaluate factual statements with strict Supported or Contradicted verdicts.
              </p>
            </div>

            {/* Card 3: Check Facts / Compare Documents */}
            <div
              className="action-card-suggest"
              onClick={() => {
                if (onSwitchTab) onSwitchTab('comparison');
                else handleSend('Compare key findings, agreements, and divergences between documents.');
              }}
            >
              <div
                style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '8px',
                  background: '#E0E7FF',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '4px',
                }}
              >
                <Compass size={15} color="#4F46E5" />
              </div>
              <h4 style={{ fontSize: '13px', fontWeight: 700, color: '#111827' }}>
                Check Facts
              </h4>
              <p style={{ fontSize: '11px', color: '#6B7280', lineHeight: 1.4 }}>
                Compare key differences, findings, and scope nuances across documents.
              </p>
            </div>
          </div>

          {/* 5. Minimalist Bottom Footer */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              width: '100%',
              marginTop: '28px',
              paddingTop: '12px',
              borderTop: '1px solid #F3F3F6',
              fontSize: '11px',
              color: '#9CA3AF',
            }}
          >
            <span>
              Join the ProofLens community for more insights · <a href="#" style={{ color: '#7C3AED', textDecoration: 'none' }}>Join Docs</a>
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Globe size={13} color="#9CA3AF" />
              <HelpCircle size={13} color="#9CA3AF" />
            </div>
          </div>
        </div>
      ) : (
        /* VIEW B: ACTIVE CONVERSATION STREAM (With docked Prompt Card) */
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', flex: 1 }}>
          {/* Header Bar within Chat */}
          <div
            style={{
              padding: '12px 24px',
              borderBottom: '1px solid #F3F3F6',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: '#FFFFFF',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: '#10B981',
                }}
              />
              <span style={{ fontSize: '13px', fontWeight: 600, color: '#111827' }}>
                Active Evidence Investigation
              </span>
              <span style={{ fontSize: '11px', color: '#9CA3AF' }}>
                ({messages.length} messages)
              </span>
            </div>

            <button
              onClick={() => setMessages([])}
              className="btn-pill"
              style={{ fontSize: '11px', padding: '4px 10px' }}
              title="Return to Welcome screen"
            >
              <RotateCcw size={12} /> New Conversation
            </button>
          </div>

          {/* Messages Scroll Area */}
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '20px',
              maxWidth: '860px',
              margin: '0 auto',
              width: '100%',
            }}
          >
            {messages.map((msg) => {
              const isUser = msg.sender === 'user';
              const isAbstained =
                msg.qaData?.status === 'insufficient_evidence' ||
                msg.content.toLowerCase().includes('insufficient evidence');

              return (
                <div
                  key={msg.id}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: isUser ? 'flex-end' : 'flex-start',
                    gap: '4px',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '10px',
                      maxWidth: '85%',
                      flexDirection: isUser ? 'row-reverse' : 'row',
                    }}
                  >
                    {/* Avatar Icon */}
                    <div
                      style={{
                        width: '28px',
                        height: '28px',
                        borderRadius: '50%',
                        background: isUser
                          ? 'linear-gradient(135deg, #A855F7 0%, #EC4899 100%)'
                          : 'linear-gradient(135deg, #7C3AED 0%, #A855F7 100%)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#FFFFFF',
                        fontSize: '11px',
                        fontWeight: 700,
                        flexShrink: 0,
                      }}
                    >
                      {isUser ? userName.slice(0, 1).toUpperCase() : <Sparkles size={14} />}
                    </div>

                    {/* Message Bubble Card */}
                    <div
                      style={{
                        background: isUser ? '#18181B' : '#F9F9FB',
                        color: isUser ? '#FFFFFF' : '#111827',
                        padding: '14px 18px',
                        borderRadius: isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                        border: isUser ? 'none' : '1px solid #ECECF1',
                        boxShadow: '0 2px 6px rgba(0,0,0,0.03)',
                        fontSize: '14px',
                        lineHeight: 1.6,
                      }}
                    >
                      {/* Explicit Abstention Alert Banner */}
                      {!isUser && isAbstained && (
                        <div
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            background: '#FFFBEB',
                            border: '1px solid #FCD34D',
                            color: '#B45309',
                            padding: '8px 12px',
                            borderRadius: '8px',
                            marginBottom: '10px',
                            fontSize: '12px',
                            fontWeight: 600,
                          }}
                        >
                          <AlertTriangle size={15} color="#D97706" />
                          <span>Explicit Abstention: Evidence is insufficient or out-of-scope.</span>
                        </div>
                      )}

                      <div>{msg.content}</div>

                      {/* Assistant Verified Citations */}
                      {!isUser && msg.qaData && msg.qaData.citations && msg.qaData.citations.length > 0 && (
                        <div
                          style={{
                            marginTop: '12px',
                            paddingTop: '10px',
                            borderTop: '1px solid #E5E7EB',
                            display: 'flex',
                            flexWrap: 'wrap',
                            alignItems: 'center',
                            gap: '6px',
                          }}
                        >
                          <span style={{ fontSize: '11px', fontWeight: 600, color: '#6B7280' }}>
                            Verified Sources:
                          </span>
                          {msg.qaData.citations.map((c, idx) => (
                            <button
                              key={c.chunk_id || idx}
                              onClick={() => onOpenCitation(c)}
                              className="citation-tag"
                              title={`Inspect Page ${c.page_number} in ${c.document_name || c.filename || 'Document'}`}
                            >
                              <span>[{idx + 1}]</span>
                              <span>{c.document_name || c.filename || 'Document'} (p.{c.page_number})</span>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  <span
                    style={{
                      fontSize: '10px',
                      color: '#9CA3AF',
                      padding: '0 38px',
                    }}
                  >
                    {msg.timestamp}
                  </span>
                </div>
              );
            })}

            {/* Loading Indicator Bubble */}
            {loading && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div
                  style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, #7C3AED 0%, #A855F7 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#FFFFFF',
                  }}
                >
                  <Sparkles size={14} />
                </div>
                <div
                  style={{
                    background: '#F9F9FB',
                    border: '1px solid #ECECF1',
                    padding: '12px 18px',
                    borderRadius: '18px 18px 18px 4px',
                    fontSize: '13px',
                    color: '#6B7280',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                  }}
                >
                  <div
                    style={{
                      width: '12px',
                      height: '12px',
                      borderRadius: '50%',
                      border: '2px solid #C4B5FD',
                      borderTopColor: '#7C3AED',
                      animation: 'spin 1s linear infinite',
                    }}
                  />
                  <span>Retrieving vector chunks and verifying page citations...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Docked Prompt Card at bottom */}
          <div
            style={{
              padding: '12px 24px 20px',
              borderTop: '1px solid #F3F3F6',
              background: '#FFFFFF',
              maxWidth: '860px',
              margin: '0 auto',
              width: '100%',
            }}
          >
            <div className="prompt-box-card" style={{ padding: '12px 16px 8px' }}>
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Ask follow-up question..."
                rows={1}
                style={{
                  width: '100%',
                  border: 'none',
                  outline: 'none',
                  resize: 'none',
                  fontSize: '14px',
                  fontFamily: 'var(--font-sans)',
                  color: '#111827',
                  background: 'transparent',
                }}
              />

              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  paddingTop: '6px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <button
                    type="button"
                    onClick={() => setDeeperResearch(!deeperResearch)}
                    className={`deeper-research-pill ${deeperResearch ? 'active' : ''}`}
                    style={{ padding: '3px 10px', fontSize: '10px' }}
                  >
                    <Atom size={12} />
                    <span>Deeper Research</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploadingDoc}
                    className="btn-pill"
                    style={{ fontSize: '10px', padding: '3px 8px' }}
                  >
                    <Paperclip size={11} />
                    <span>Attach</span>
                  </button>
                </div>

                <button
                  type="button"
                  onClick={() => handleSend()}
                  disabled={!query.trim() || loading}
                  className="btn-send-circle"
                  style={{ width: '30px', height: '30px' }}
                >
                  <ArrowUp size={14} />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
