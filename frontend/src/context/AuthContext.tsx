import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserProfile, AuthResponse } from '../types';

import { API_BASE_URL } from '../config';
const TOKEN_KEY = 'decisio_auth_token';


interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: str, password: str, rememberMe?: boolean) => Promise<void>;
  signup: (email: str, password: str, fullName?: str, rememberMe?: boolean) => Promise<void>;
  sendOtp: (email: str) => Promise<{ message: string; otp_debug?: string }>;
  verifyOtp: (email: str, otpCode: str, password: str, fullName?: str, rememberMe?: boolean) => Promise<void>;
  googleLogin: (email: str, fullName?: str, idToken?: str, rememberMe?: boolean) => Promise<void>;
  forgotPassword: (email: str) => Promise<string>;
  logout: () => void;
  getAuthHeaders: () => Record<string, string>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(
    localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY)
  );
  const [loading, setLoading] = useState<boolean>(true);

  const fetchCurrentUser = async (authToken: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      });
      if (response.ok) {
        const userData: UserProfile = await response.json();
        setUser(userData);
      } else {
        localStorage.removeItem(TOKEN_KEY);
        sessionStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setUser(null);
      }
    } catch {
      // Ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchCurrentUser(token);
    } else {
      setLoading(false);
    }
  }, [token]);

  const saveAuthSession = (authToken: string, userData: UserProfile, rememberMe: boolean = true) => {
    if (rememberMe) {
      localStorage.setItem(TOKEN_KEY, authToken);
      sessionStorage.removeItem(TOKEN_KEY);
    } else {
      sessionStorage.setItem(TOKEN_KEY, authToken);
      localStorage.removeItem(TOKEN_KEY);
    }
    setToken(authToken);
    setUser(userData);
  };

  const login = async (email: str, password: str, rememberMe: boolean = true) => {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      let errMsg = 'Failed to sign in. Please check your credentials.';
      try {
        const errData = await response.json();
        if (errData.detail) errMsg = errData.detail;
      } catch {
        // Ignore
      }
      throw new Error(errMsg);
    }

    const data: AuthResponse = await response.json();
    saveAuthSession(data.access_token, data.user, rememberMe);
  };

  const sendOtp = async (email: str): Promise<{ message: string; otp_debug?: string }> => {
    const response = await fetch(`${API_BASE_URL}/auth/send-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });

    if (!response.ok) {
      let errMsg = 'Failed to send verification code.';
      try {
        const errData = await response.json();
        if (errData.detail) errMsg = errData.detail;
      } catch {
        // Ignore
      }
      throw new Error(errMsg);
    }

    return await response.json();
  };

  const verifyOtp = async (email: str, otpCode: str, password: str, fullName?: str, rememberMe: boolean = true) => {
    const response = await fetch(`${API_BASE_URL}/auth/verify-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, otp_code: otpCode, password, full_name: fullName }),
    });

    if (!response.ok) {
      let errMsg = 'Verification failed. Incorrect code or expired.';
      try {
        const errData = await response.json();
        if (errData.detail) errMsg = errData.detail;
      } catch {
        // Ignore
      }
      throw new Error(errMsg);
    }

    const data: AuthResponse = await response.json();
    saveAuthSession(data.access_token, data.user, rememberMe);
  };

  const signup = async (email: str, password: str, fullName?: str, rememberMe: boolean = true) => {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, full_name: fullName }),
    });

    if (!response.ok) {
      let errMsg = 'Failed to create account.';
      try {
        const errData = await response.json();
        if (errData.detail) errMsg = errData.detail;
      } catch {
        // Ignore
      }
      throw new Error(errMsg);
    }

    const data: AuthResponse = await response.json();
    saveAuthSession(data.access_token, data.user, rememberMe);
  };

  const googleLogin = async (email: str, fullName?: str, idToken?: str, rememberMe: boolean = true) => {
    const response = await fetch(`${API_BASE_URL}/auth/oauth/google`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, full_name: fullName, id_token: idToken }),
    });

    if (!response.ok) {
      let errMsg = 'Google authentication failed.';
      try {
        const errData = await response.json();
        if (errData.detail) errMsg = errData.detail;
      } catch {
        // Ignore
      }
      throw new Error(errMsg);
    }

    const data: AuthResponse = await response.json();
    saveAuthSession(data.access_token, data.user, rememberMe);
  };

  const forgotPassword = async (email: str): Promise<string> => {
    const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });

    if (!response.ok) {
      let errMsg = 'Failed to process password reset.';
      try {
        const errData = await response.json();
        if (errData.detail) errMsg = errData.detail;
      } catch {
        // Ignore
      }
      throw new Error(errMsg);
    }

    const data = await response.json();
    return data.message || 'Reset link sent.';
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  };

  const getAuthHeaders = (): Record<string, string> => {
    if (token) {
      return { 'Authorization': `Bearer ${token}` };
    }
    return {};
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        loading,
        login,
        signup,
        sendOtp,
        verifyOtp,
        googleLogin,
        forgotPassword,
        logout,
        getAuthHeaders,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
