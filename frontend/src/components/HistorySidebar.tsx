import React, { useEffect, useState } from 'react';
import { AnalysisHistoryItem } from '../types';
import { useAuth } from '../context/AuthContext';
import { AuthModal } from './AuthModal';

import { API_BASE_URL } from '../config';


interface HistorySidebarProps {
  onSelectAnalysis: (id: number) => void;
  onNewAnalysis: () => void;
  selectedId: number | null;
  refreshTrigger: number;
}

export const HistorySidebar: React.FC<HistorySidebarProps> = ({
  onSelectAnalysis,
  onNewAnalysis,
  selectedId,
  refreshTrigger,
}) => {
  const { getAuthHeaders, isAuthenticated, user } = useAuth();
  const [historyItems, setHistoryItems] = useState<AnalysisHistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [authModalOpen, setAuthModalOpen] = useState<boolean>(false);

  const fetchHistory = async () => {
    if (!isAuthenticated) {
      setHistoryItems([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/analyses?limit=30`, {
        headers: { ...getAuthHeaders() },
      });
      if (!response.ok) {
        throw new Error(`Failed to load history (${response.status})`);
      }
      const data: AnalysisHistoryItem[] = await response.json();
      setHistoryItems(data);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to load history.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [refreshTrigger, isAuthenticated, user]);

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    try {
      const response = await fetch(`${API_BASE_URL}/analyses/${id}`, {
        method: 'DELETE',
        headers: { ...getAuthHeaders() },
      });
      if (response.ok) {
        setHistoryItems((prev) => prev.filter((item) => item.id !== id));
        if (selectedId === id) {
          onNewAnalysis();
        }
      }
    } catch (err) {
      console.error('Delete error:', err);
    }
  };

  const formatRelativeTime = (isoString: string) => {
    if (!isoString) return '';
    try {
      const date = new Date(isoString);
      const now = new Date();
      const diffSec = Math.floor((now.getTime() - date.getTime()) / 1000);

      if (diffSec < 60) return 'Just now';
      if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
      if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
      return `${Math.floor(diffSec / 86400)}d ago`;
    } catch {
      return '';
    }
  };

  return (
    <>
      <aside className="history-sidebar">
        <button
          type="button"
          onClick={() => {
            if (!isAuthenticated) {
              setAuthModalOpen(true);
            } else {
              onNewAnalysis();
            }
          }}
          className="btn-new-analysis"
        >
          <span>+ New Analysis</span>
        </button>

        <div className="sidebar-header">
          <span className="sidebar-title">
            {user ? `${user.full_name || 'My'} History` : 'Recent Analyses'}
          </span>
          <span className="sidebar-count">{historyItems.length}</span>
        </div>

        {!isAuthenticated ? (
          <div style={{ padding: '1.25rem 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
            <p style={{ margin: '0 0 0.75rem 0', color: 'var(--text-secondary)' }}>
              Sign in to view and save your decision history.
            </p>
            <button
              type="button"
              onClick={() => setAuthModalOpen(true)}
              style={{
                backgroundColor: '#ffffff',
                border: '1px solid var(--border-color)',
                color: 'var(--text-primary)',
                padding: '0.35rem 0.75rem',
                borderRadius: '6px',
                fontSize: '0.8125rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              Sign In
            </button>
          </div>
        ) : (
          <>
            {loading && (
              <div style={{ padding: '1rem 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                <span>Loading history...</span>
              </div>
            )}

            {error && (
              <div style={{ padding: '0.75rem', backgroundColor: 'var(--status-error-bg)', color: 'var(--status-error-text)', borderRadius: '6px', fontSize: '0.8125rem' }}>
                {error}
              </div>
            )}

            {!loading && !error && historyItems.length === 0 && (
              <div style={{ padding: '1.5rem 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                <p style={{ margin: 0 }}>No saved analyses yet.</p>
                <span style={{ fontSize: '0.75rem', display: 'block', marginTop: '0.25rem' }}>
                  Submit a query to evaluate it!
                </span>
              </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '550px', overflowY: 'auto' }}>
              {historyItems.map((item) => {
                const isSelected = selectedId === item.id;
                return (
                  <div
                    key={item.id}
                    onClick={() => onSelectAnalysis(item.id)}
                    className={`history-card ${isSelected ? 'active' : ''}`}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem' }}>
                      <span className="history-card-title">
                        {item.problem}
                      </span>
                      <button
                        type="button"
                        onClick={(e) => handleDelete(e, item.id)}
                        title="Delete analysis"
                        className="btn-delete-item"
                      >
                        Delete
                      </button>
                    </div>

                    <div className="history-card-meta">
                      <span className="type-tag">
                        {item.request_type}
                      </span>
                      <span>{formatRelativeTime(item.created_at)}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </aside>

      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        initialMode="login"
      />
    </>
  );
};
