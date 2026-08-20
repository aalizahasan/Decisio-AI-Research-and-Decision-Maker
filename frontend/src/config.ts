// Centralized API Configuration Helper for Local Dev & Production Deployments
export const getApiBaseUrl = (): string => {
  if (typeof window !== 'undefined' && window.location.hostname.includes('vercel.app')) {
    return ''; // On Vercel, always use relative routes for unified single-domain deployment
  }
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (envUrl && envUrl.trim() !== '') {
    return envUrl.trim();
  }
  return import.meta.env.PROD ? '' : 'http://127.0.0.1:8000';
};

export const API_BASE_URL: string = getApiBaseUrl();
