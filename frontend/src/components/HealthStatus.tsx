import React, { useEffect, useState } from 'react';
import { HealthResponse } from '../types';
import { API_BASE_URL } from '../config';

export const HealthStatus: React.FC = () => {
  const [status, setStatus] = useState<'checking' | 'healthy' | 'offline'>('checking');

  useEffect(() => {
    let isMounted = true;

    const checkHealth = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/health`, { cache: 'no-store' });
        if (response.ok) {
          const data: HealthResponse = await response.json();
          if (data.status === 'healthy' && isMounted) {
            setStatus('healthy');
          } else if (isMounted) {
            setStatus('offline');
          }
        } else if (isMounted) {
          setStatus('offline');
        }
      } catch (error) {
        if (isMounted) {
          setStatus('offline');
        }
      }
    };

    checkHealth();
    const intervalId = setInterval(checkHealth, 5000);

    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
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
