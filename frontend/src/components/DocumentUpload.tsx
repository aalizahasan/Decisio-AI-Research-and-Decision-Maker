import React, { useState } from 'react';
import { DocumentItem } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

interface DocumentUploadProps {
  onDocumentSelected: (doc: DocumentItem | null) => void;
  selectedDoc: DocumentItem | null;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({
  onDocumentSelected,
  selectedDoc,
}) => {
  const [uploading, setUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf') && !file.type.includes('pdf')) {
      setError('Unsupported file type. Please upload a valid PDF document.');
      return;
    }

    setError(null);
    setUploading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/documents/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        let errMsg = `Upload failed with status ${response.status}`;
        try {
          const errData = await response.json();
          if (errData.detail) errMsg = errData.detail;
        } catch {
          // Ignore
        }
        throw new Error(errMsg);
      }

      const data = await response.json();
      const newDoc: DocumentItem = {
        id: data.document_id,
        filename: data.filename,
        file_type: 'pdf',
        created_at: new Date().toISOString(),
        chunks_count: data.chunks_created,
      };

      onDocumentSelected(newDoc);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to upload and index PDF document.');
      }
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleRemove = () => {
    onDocumentSelected(null);
    setError(null);
  };

  return (
    <div className="form-group" style={{ marginBottom: '1.25rem' }}>
      <label className="form-label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span>Attach Document (Optional PDF Reference)</span>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 400 }}>
          PDF format up to 10MB
        </span>
      </label>

      {selectedDoc ? (
        <div className="selected-doc-badge">
          <div>
            <strong className="doc-name">{selectedDoc.filename}</strong>
            <p className="doc-subtext">{selectedDoc.chunks_count} text sections indexed for reference</p>
          </div>
          <button type="button" onClick={handleRemove} className="remove-doc-btn">
            Remove
          </button>
        </div>
      ) : (
        <div className="upload-dropzone">
          <input
            type="file"
            id="pdf-upload"
            accept=".pdf,application/pdf"
            onChange={handleFileChange}
            disabled={uploading}
            style={{ display: 'none' }}
          />
          <label htmlFor="pdf-upload" className="dropzone-label">
            {uploading ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                <span className="spinner" style={{ borderColor: 'rgba(30, 41, 59, 0.2)', borderTopColor: '#1e293b' }}></span>
                <span>Processing document sections...</span>
              </div>
            ) : (
              <div>
                <span style={{ display: 'block', color: 'var(--text-primary)', fontWeight: 600 }}>
                  Click to attach reference PDF document
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginTop: '0.2rem' }}>
                  Extracts text and grounds decision output in your document data
                </span>
              </div>
            )}
          </label>
        </div>
      )}

      {error && (
        <div className="error-banner" style={{ marginTop: '0.5rem' }}>
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};
