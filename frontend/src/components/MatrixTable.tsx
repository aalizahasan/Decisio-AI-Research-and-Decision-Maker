import React from 'react';
import { DecisionMatrixData } from '../types';

interface MatrixTableProps {
  matrix: DecisionMatrixData;
}

export const MatrixTable: React.FC<MatrixTableProps> = ({ matrix }) => {
  if (!matrix || !matrix.options || !matrix.criteria || matrix.options.length < 2) {
    return null;
  }

  return (
    <div className="matrix-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <h4 className="matrix-title" style={{ margin: 0 }}>
          Decision Comparison Matrix
        </h4>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', backgroundColor: '#f1f5f9', padding: '0.25rem 0.6rem', borderRadius: '4px', border: '1px solid var(--border-color)' }}>
          Weighted Calculation
        </span>
      </div>

      {/* Rankings Banner */}
      <div style={{
        display: 'flex',
        gap: '0.75rem',
        flexWrap: 'wrap',
        marginBottom: '1.25rem',
        padding: '0.75rem 1rem',
        backgroundColor: '#f8fafc',
        borderRadius: '8px',
        border: '1px solid var(--border-color)'
      }}>
        <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)', alignSelf: 'center' }}>
          Calculated Ranking:
        </span>
        {matrix.rankings.map((r) => (
          <span
            key={r.option}
            className={`rank-badge ${r.rank === 1 ? 'top' : 'secondary'}`}
          >
            <span>#{r.rank} {r.option}</span>
            <span style={{ opacity: 0.8, fontWeight: 400, marginLeft: '0.25rem' }}>({r.score.toFixed(2)})</span>
          </span>
        ))}
      </div>

      {/* Table */}
      <div style={{ overflowX: 'auto' }}>
        <table className="matrix-table">
          <thead>
            <tr>
              <th>Evaluation Criteria</th>
              <th style={{ textAlign: 'center' }}>Weight</th>
              {matrix.options.map((opt) => (
                <th key={opt} style={{ textAlign: 'center' }}>
                  {opt}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrix.criteria.map((c) => (
              <tr key={c.name}>
                <td style={{ fontWeight: 500 }}>{c.name}</td>
                <td style={{ textAlign: 'center', fontWeight: 600, color: 'var(--accent-blue)' }}>
                  {Math.round(c.weight * 100)}%
                </td>
                {matrix.options.map((opt) => {
                  const rating = matrix.scores[opt]?.[c.name] ?? '-';
                  return (
                    <td key={opt} style={{ textAlign: 'center', fontWeight: 600 }}>
                      {rating} <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>/10</span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
