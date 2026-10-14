'use client';

import React, { useState } from 'react';
import { X, Lock, Mail, User as UserIcon, Sparkles, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api';
import { User } from '@/types';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAuthSuccess: (user: User) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  onAuthSuccess,
}) => {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleDemoLogin = async () => {
    setLoading(true);
    setError(null);
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
      api.setToken(tokenRes.access_token);
      const user = await api.auth.getMe();
      onAuthSuccess(user);
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Demo login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isRegister) {
        const tokenRes = await api.auth.register(email, password, fullName);
        api.setToken(tokenRes.access_token);
      } else {
        const tokenRes = await api.auth.login(email, password);
        api.setToken(tokenRes.access_token);
      }

      const user = await api.auth.getMe();
      onAuthSuccess(user);
      onClose();
    } catch (err: unknown) {
      if (err instanceof Error) {
        if (!isRegister && err.message.toLowerCase().includes('incorrect email or password')) {
          setError("Incorrect email or password. If you haven't created an account yet, click 'Create one' below.");
        } else {
          setError(err.message);
        }
      } else {
        setError('Authentication failed. Please try again.');
      }
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

        <div style={{ textAlign: 'center', marginBottom: 'var(--space-4)' }}>
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--color-brand-gradient)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: 'var(--space-2)',
              boxShadow: 'var(--shadow-sm)',
            }}
          >
            <Sparkles size={20} color="#FFFFFF" />
          </div>
          <h2 style={{ fontSize: 'var(--text-lg)', fontWeight: 'var(--weight-bold)' }}>
            {isRegister ? 'Create Account' : 'Welcome to ProofLens AI'}
          </h2>
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', marginTop: 'var(--space-1)' }}>
            {isRegister
              ? 'Create your dedicated, tenant-isolated account.'
              : 'Sign in to access your private workspaces and documents.'}
          </p>
        </div>

        {/* Segmented Auth Tabs */}
        <div
          style={{
            display: 'flex',
            background: '#F4F4F5',
            padding: '3px',
            borderRadius: '10px',
            marginBottom: 'var(--space-4)',
          }}
        >
          <button
            type="button"
            onClick={() => {
              setIsRegister(false);
              setError(null);
            }}
            style={{
              flex: 1,
              padding: '7px 12px',
              borderRadius: '8px',
              border: 'none',
              background: !isRegister ? '#FFFFFF' : 'transparent',
              color: !isRegister ? '#18181B' : '#71717A',
              boxShadow: !isRegister ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
              fontWeight: !isRegister ? 600 : 500,
              fontSize: '12px',
              cursor: 'pointer',
              transition: 'all 150ms ease',
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setIsRegister(true);
              setError(null);
            }}
            style={{
              flex: 1,
              padding: '7px 12px',
              borderRadius: '8px',
              border: 'none',
              background: isRegister ? '#FFFFFF' : 'transparent',
              color: isRegister ? '#18181B' : '#71717A',
              boxShadow: isRegister ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
              fontWeight: isRegister ? 600 : 500,
              fontSize: '12px',
              cursor: 'pointer',
              transition: 'all 150ms ease',
            }}
          >
            Create Account
          </button>
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
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
              marginBottom: 'var(--space-4)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <AlertCircle size={15} style={{ flexShrink: 0 }} />
              <span>{error}</span>
            </div>
            {!isRegister && error.toLowerCase().includes('incorrect email or password') && (
              <button
                type="button"
                onClick={() => {
                  setIsRegister(true);
                  setError(null);
                }}
                style={{
                  alignSelf: 'flex-start',
                  background: 'none',
                  border: 'none',
                  color: '#7C3AED',
                  fontWeight: 600,
                  fontSize: '11px',
                  cursor: 'pointer',
                  padding: 0,
                  textDecoration: 'underline',
                  marginTop: '2px',
                }}
              >
                Click here to create a new account with these credentials →
              </button>
            )}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {isRegister && (
            <div>
              <label style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', display: 'block', marginBottom: 'var(--space-1)' }}>
                Full Name
              </label>
              <div style={{ position: 'relative' }}>
                <UserIcon size={15} color="var(--color-text-muted)" style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)' }} />
                <input
                  type="text"
                  className="input-field"
                  style={{ paddingLeft: '2.25rem' }}
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Srushti Bore"
                  required
                />
              </div>
            </div>
          )}

          <div>
            <label style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', display: 'block', marginBottom: 'var(--space-1)' }}>
              Email Address
            </label>
            <div style={{ position: 'relative' }}>
              <Mail size={15} color="var(--color-text-muted)" style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="email"
                className="input-field"
                style={{ paddingLeft: '2.25rem' }}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@organization.com"
                required
              />
            </div>
          </div>

          <div>
            <label style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', display: 'block', marginBottom: 'var(--space-1)' }}>
              {isRegister ? 'Password (minimum 8 characters)' : 'Password'}
            </label>
            <div style={{ position: 'relative' }}>
              <Lock size={15} color="var(--color-text-muted)" style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="password"
                className="input-field"
                style={{ paddingLeft: '2.25rem' }}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                minLength={isRegister ? 8 : undefined}
                required
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
            style={{ width: '100%', padding: 'var(--space-3)', marginTop: 'var(--space-2)' }}
          >
            {loading ? 'Authenticating...' : isRegister ? 'Register & Enter Workspace' : 'Sign In'}
          </button>
        </form>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: '14px 0 10px' }}>
          <div style={{ flex: 1, height: '1px', backgroundColor: '#E4E4E7' }} />
          <span style={{ fontSize: '11px', color: '#A1A1AA' }}>OR</span>
          <div style={{ flex: 1, height: '1px', backgroundColor: '#E4E4E7' }} />
        </div>

        <button
          type="button"
          onClick={handleDemoLogin}
          disabled={loading}
          className="btn-secondary"
          style={{ width: '100%', padding: '10px 14px', fontSize: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
        >
          <Sparkles size={14} color="#7C3AED" /> Try Demo Account
        </button>

        <div style={{ textAlign: 'center', marginTop: 'var(--space-4)' }}>
          <button
            type="button"
            onClick={() => {
              setIsRegister(!isRegister);
              setError(null);
            }}
            className="btn-ghost"
            style={{ fontSize: 'var(--text-xs)' }}
          >
            {isRegister
              ? 'Already have an account? Sign in here'
              : "Don't have an account? Create one"}
          </button>
        </div>
      </div>
    </div>
  );
};
