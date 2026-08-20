import React, { useState } from 'react';
import { HealthStatus } from './HealthStatus';
import { useAuth } from '../context/AuthContext';
import { AuthModal } from './AuthModal';

export const Header: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState<'login' | 'signup'>('login');
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const openAuth = (mode: 'login' | 'signup') => {
    setAuthModalMode(mode);
    setAuthModalOpen(true);
    setUserMenuOpen(false);
  };

  const getUserInitials = (name?: string, email?: string): string => {
    if (name && name.trim()) {
      const parts = name.trim().split(' ');
      if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
      return name.slice(0, 2).toUpperCase();
    }
    if (email) return email.slice(0, 2).toUpperCase();
    return 'U';
  };

  return (
    <>
      <header className="header">
        <div className="container header-content">
          <div className="logo-section">
            <span className="logo-badge">Decisio</span>
            <span className="logo-title">Decisio</span>
            <span className="logo-subtitle">Clear Answers & Smart Choices</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
            <HealthStatus />

            {isAuthenticated && user ? (
              <div style={{ position: 'relative' }}>
                <button
                  type="button"
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  style={{
                    backgroundColor: '#ffffff',
                    border: '1px solid var(--border-color)',
                    borderRadius: '9999px',
                    padding: '0.25rem 0.75rem 0.25rem 0.35rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    cursor: 'pointer',
                    boxShadow: 'var(--shadow-sm)'
                  }}
                >
                  <div style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '50%',
                    backgroundColor: 'var(--accent-primary)',
                    color: '#ffffff',
                    fontWeight: 700,
                    fontSize: '0.75rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    {getUserInitials(user.full_name, user.email)}
                  </div>
                  <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {user.full_name || user.email.split('@')[0]}
                  </span>
                </button>

                {userMenuOpen && (
                  <div style={{
                    position: 'absolute',
                    right: 0,
                    top: 'calc(100% + 0.5rem)',
                    backgroundColor: '#ffffff',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    padding: '0.5rem 0',
                    width: '220px',
                    boxShadow: 'var(--shadow-md)',
                    zIndex: 200
                  }}>
                    <div style={{ padding: '0.5rem 1rem', borderBottom: '1px solid var(--border-color)' }}>
                      <p style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
                        {user.full_name || 'User Account'}
                      </p>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: 0 }}>
                        {user.email}
                      </p>
                    </div>

                    <button
                      type="button"
                      onClick={() => {
                        setUserMenuOpen(false);
                        logout();
                      }}
                      style={{
                        width: '100%',
                        textAlign: 'left',
                        padding: '0.5rem 1rem',
                        background: 'none',
                        border: 'none',
                        color: 'var(--status-error-text)',
                        fontSize: '0.8125rem',
                        fontWeight: 600,
                        cursor: 'pointer'
                      }}
                    >
                      Sign Out
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <button
                  type="button"
                  onClick={() => openAuth('login')}
                  style={{
                    backgroundColor: 'transparent',
                    border: '1px solid var(--border-color)',
                    color: 'var(--text-primary)',
                    padding: '0.4rem 0.85rem',
                    borderRadius: '6px',
                    fontSize: '0.8125rem',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  Sign In
                </button>

                <button
                  type="button"
                  onClick={() => openAuth('signup')}
                  style={{
                    backgroundColor: 'var(--accent-primary)',
                    border: 'none',
                    color: '#ffffff',
                    padding: '0.4rem 0.85rem',
                    borderRadius: '6px',
                    fontSize: '0.8125rem',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  Get Started
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        initialMode={authModalMode}
      />
    </>
  );
};
