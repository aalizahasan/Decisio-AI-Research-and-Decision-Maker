import React, { useEffect, useState } from 'react';
import { HealthResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export const HealthStatus: React.FC = () => {
  const [status, setStatus] = useState<'checking' | 'healthy' | 'offline'>('checking');

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
          const data: HealthResponse = await response.json();
          if (data.status === 'healthy') {
            setStatus('healthy');
          } else {
            setStatus('offline');
          }
        } else {
          setStatus('offline');
        }
      } catch (error) {
        setStatus('offline');
      }
    };

    checkHealth();
  }, []);

  if (status === 'checking') {
    return (
      <div className="health-badge">
        <span className="health-dot" style={{ backgroundColor: '#94a3b8' }}></span>
        <span>Connecting API...</span>
      </div>
    );
  }

  if (status === 'healthy') {
    return (
      <div className="health-badge healthy">
        <span className="health-dot"></span>
        <span>API Online</span>
      </div>
    );
  }

  return (
    <div className="health-badge unhealthy">
      <span className="health-dot"></span>
      <span>API Offline</span>
    </div>
  );
};
