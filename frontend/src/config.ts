// Centralized API Configuration Helper for Local Dev & Production Deployments
export const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL !== undefined && import.meta.env.VITE_API_BASE_URL !== ''
    ? import.meta.env.VITE_API_BASE_URL
    : (import.meta.env.PROD ? '' : 'http://127.0.0.1:8000');
