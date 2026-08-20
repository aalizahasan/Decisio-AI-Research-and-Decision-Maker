import React, { useState, useEffect } from 'react';
import { DecisionInput, AnalysisResponse, DocumentItem, AnalysisDetail } from '../types';
import { DocumentUpload } from './DocumentUpload';
import { MatrixTable } from './MatrixTable';
import { MarkdownRenderer } from './MarkdownRenderer';
import { useAuth } from '../context/AuthContext';
import { AuthModal } from './AuthModal';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

interface DecisionFormProps {
  activeAnalysisId: number | null;
  onAnalysisSaved: () => void;
  onNewAnalysis: () => void;
}

export const DecisionForm: React.FC<DecisionFormProps> = ({
  activeAnalysisId,
  onAnalysisSaved,
  onNewAnalysis,
}) => {
  const { getAuthHeaders, isAuthenticated, user } = useAuth();
  const [authModalOpen, setAuthModalOpen] = useState(false);

  const [formData, setFormData] = useState<DecisionInput>({
    problem: '',
    context: '',
    constraints: '',
    response_preference: 'auto',
  });

  const [selectedDoc, setSelectedDoc] = useState<DocumentItem | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [viewingSaved, setViewingSaved] = useState<boolean>(false);

  useEffect(() => {
    if (activeAnalysisId && isAuthenticated) {
      const loadSavedAnalysis = async () => {
        setLoading(true);
        setError(null);
        try {
          const response = await fetch(`${API_BASE_URL}/analyses/${activeAnalysisId}`, {
            headers: { ...getAuthHeaders() },
          });
          if (!response.ok) {
            throw new Error(`Analysis not found (HTTP ${response.status})`);
          }
          const detail: AnalysisDetail = await response.json();
          setFormData({
            problem: detail.problem,
            context: detail.context || '',
            constraints: detail.constraints || '',
            response_preference: 'auto',
          });
          setResult({
            status: 'success',
            message: `Loaded saved analysis #${detail.id}`,
            analysis_id: detail.id,
            problem: detail.problem,
            context: detail.context,
            constraints: detail.constraints,
            analysis: detail.analysis,
            request_type: detail.request_type,
            response_depth: detail.response_depth,
            multi_agent_used: detail.multi_agent_used,
            agents_metadata: detail.agents_metadata,
            sources: detail.sources,
            matrix: detail.matrix,
          });
          setViewingSaved(true);
        } catch (err: unknown) {
          if (err instanceof Error) {
            setError(err.message);
          } else {
            setError('Failed to retrieve saved analysis.');
          }
        } finally {
          setLoading(false);
        }
      };
      loadSavedAnalysis();
    } else {
      setFormData({
        problem: '',
        context: '',
        constraints: '',
        response_preference: 'auto',
      });
      setResult(null);
      setError(null);
      setViewingSaved(false);
    }
  }, [activeAnalysisId, isAuthenticated, user]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isAuthenticated) {
      setAuthModalOpen(true);
      return;
    }

    if (!formData.problem.trim()) {
      setError('Please enter a decision statement or question.');
      return;
    }

    setError(null);
    setLoading(true);
    setResult(null);
    setViewingSaved(false);

    const payload: DecisionInput = {
      ...formData,
      document_id: selectedDoc ? selectedDoc.id : undefined,
    };

    try {
      const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify(payload),
      });

      if (response.status === 401) {
        setAuthModalOpen(true);
        throw new Error('Authentication required. Please sign in to evaluate queries.');
      }

      if (!response.ok) {
        let errorMessage = `Server returned HTTP ${response.status} (${response.statusText})`;
        try {
          const errData = await response.json();
          if (errData.detail) {
            errorMessage = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
          }
        } catch {
          // Ignore
        }
        throw new Error(errorMessage);
      }

      const data: AnalysisResponse = await response.json();
      setResult(data);
      onAnalysisSaved();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred while generating analysis.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="decision-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
          <div>
            <h2 className="workspace-title">Decision Workspace</h2>
            <p className="workspace-subtitle">
              Evaluate choices, analyze technical tradeoffs, or ask complex questions.
            </p>
          </div>
          {viewingSaved && (
            <button
              type="button"
              onClick={onNewAnalysis}
              style={{
                backgroundColor: '#ffffff',
                border: '1px solid var(--border-color)',
                color: 'var(--text-primary)',
                padding: '0.4rem 0.85rem',
                borderRadius: '6px',
                fontSize: '0.8125rem',
                cursor: 'pointer',
                fontWeight: 600
              }}
            >
              Start New Query
            </button>
          )}
        </div>

        {!isAuthenticated && (
          <div style={{
            backgroundColor: '#eff6ff',
            border: '1px solid #bfdbfe',
            borderRadius: '10px',
            padding: '1rem 1.25rem',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '1rem',
            flexWrap: 'wrap'
          }}>
            <div>
              <strong style={{ color: '#1e40af', fontSize: '0.9375rem', display: 'block' }}>
                Authentication Required
              </strong>
              <p style={{ color: '#1d4ed8', fontSize: '0.8125rem', margin: '0.2rem 0 0 0' }}>
                Please sign in or create an account to evaluate queries and save decision history.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setAuthModalOpen(true)}
              style={{
                backgroundColor: 'var(--accent-primary)',
                color: '#ffffff',
                border: 'none',
                padding: '0.45rem 1rem',
                borderRadius: '6px',
                fontSize: '0.8125rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              Sign In / Register
            </button>
          </div>
        )}

        {viewingSaved && (
          <div style={{
            backgroundColor: '#eff6ff',
            border: '1px solid #bfdbfe',
            borderRadius: '8px',
            padding: '0.75rem 1rem',
            marginBottom: '1.5rem',
            fontSize: '0.875rem',
            color: '#1d4ed8',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <span>Viewing Saved Analysis #{activeAnalysisId} from History</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="problem" className="form-label">
              What decision or question would you like to evaluate? <span style={{ color: '#dc2626', fontWeight: 'bold' }}>*</span>
            </label>
            <input
              type="text"
              id="problem"
              name="problem"
              value={formData.problem}
              onChange={handleChange}
              placeholder="e.g. 'Should our startup migrate from AWS to Azure?' or 'React Native vs Flutter'"
              className="form-input"
              disabled={loading}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
            <div className="form-group">
              <label htmlFor="context" className="form-label">
                Background Context (Optional)
              </label>
              <textarea
                id="context"
                name="context"
                value={formData.context}
                onChange={handleChange}
                placeholder="Relevant team, codebase, or environment details..."
                rows={2}
                className="form-textarea"
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="constraints" className="form-label">
                Key Constraints & Budget (Optional)
              </label>
              <textarea
                id="constraints"
                name="constraints"
                value={formData.constraints}
                onChange={handleChange}
                placeholder="Timeline, financial budget, technical limits..."
                rows={2}
                className="form-textarea"
                disabled={loading}
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.25rem' }}>
            <div className="form-group" style={{ flex: '1 1 200px', marginBottom: 0 }}>
              <label htmlFor="response_preference" className="form-label">
                Response Length Preference
              </label>
              <select
                id="response_preference"
                name="response_preference"
                value={formData.response_preference}
                onChange={handleChange}
                className="form-select"
                disabled={loading}
              >
                <option value="auto">Standard (Auto-adapted)</option>
                <option value="concise">Brief (Short & Direct)</option>
                <option value="detailed">Detailed (Comprehensive Analysis)</option>
              </select>
            </div>
          </div>

          <DocumentUpload
            selectedDoc={selectedDoc}
            onDocumentSelected={(doc) => setSelectedDoc(doc)}
          />

          {error && (
            <div className="error-banner">
              <span>{error}</span>
            </div>
          )}

          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? (
              <>
                <span className="spinner"></span>
                <span>Evaluating Query...</span>
              </>
            ) : !isAuthenticated ? (
              <span>Sign In to Evaluate Query</span>
            ) : (
              <span>Evaluate Query</span>
            )}
          </button>
        </form>

        {result && (
          <div className="result-card">
            <div className="result-badge-row">
              <div className="result-status">
                <span className="health-dot"></span>
                <span>Analysis Complete</span>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {result.multi_agent_used && (
                  <span className="badge-tag deep-mode">
                    Deep Analysis Mode
                  </span>
                )}
                <span className="badge-tag">
                  Category: {result.request_type || 'General'}
                </span>
                <span className="badge-tag">
                  Depth: {result.response_depth || 'Standard'}
                </span>
              </div>
            </div>

            {result.multi_agent_used && result.agents_metadata && result.agents_metadata.length > 0 && (
              <div style={{
                backgroundColor: '#f8fafc',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                padding: '0.75rem 1rem',
                marginTop: '0.5rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                flexWrap: 'wrap'
              }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Analysis Dimensions:
                </span>
                {result.agents_metadata.map((ag, idx) => (
                  <span key={idx} style={{
                    backgroundColor: '#ffffff',
                    border: '1px solid var(--border-color)',
                    borderRadius: '4px',
                    padding: '0.15rem 0.5rem',
                    fontSize: '0.75rem',
                    color: 'var(--text-secondary)',
                    textTransform: 'capitalize'
                  }}>
                    {ag.role === 'research' ? 'Research & Evidence' : ag.role === 'risk' ? 'Risk Analysis' : ag.role === 'tradeoff' ? 'Trade-offs' : ag.role}
                  </span>
                ))}
                <span style={{
                  backgroundColor: '#ffffff',
                  border: '1px solid var(--accent-blue)',
                  borderRadius: '4px',
                  padding: '0.15rem 0.5rem',
                  fontSize: '0.75rem',
                  color: 'var(--accent-blue)',
                  fontWeight: 600
                }}>
                  Synthesized Recommendation
                </span>
              </div>
            )}

            {result.analysis && (
              <div className="analysis-box">
                <MarkdownRenderer content={result.analysis} />
              </div>
            )}

            {result.matrix && (
              <MatrixTable matrix={result.matrix} />
            )}

            {result.sources && result.sources.length > 0 && (
              <div style={{
                backgroundColor: '#f8fafc',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                padding: '1rem',
                marginTop: '0.5rem'
              }}>
                <strong style={{ color: 'var(--text-secondary)', display: 'block', marginBottom: '0.5rem', fontSize: '0.8125rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Document References ({result.sources.length}):
                </strong>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {result.sources.map((src, index) => (
                    <span key={index} style={{
                      backgroundColor: '#ffffff',
                      border: '1px solid var(--border-color)',
                      borderRadius: '6px',
                      padding: '0.3rem 0.6rem',
                      fontSize: '0.8125rem',
                      color: 'var(--text-secondary)'
                    }}>
                      Document: <strong>{src.filename}</strong> — Page {src.page_number || 'N/A'}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        initialMode="login"
      />
    </>
  );
};
