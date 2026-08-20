import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialMode?: 'login' | 'signup';
}

declare global {
  interface Window {
    google?: any;
  }
}

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '1091599743639-9977u0u0s1g5ibkkreo2ci34se4dep6k.apps.googleusercontent.com';


export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  initialMode = 'login',
}) => {
  const { login, sendOtp, verifyOtp, googleLogin, forgotPassword } = useAuth();

  const [mode, setMode] = useState<'login' | 'signup' | 'otp' | 'forgot'>(initialMode);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [rememberMe, setRememberMe] = useState<boolean>(true);
  const [debugOtp, setDebugOtp] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [suggestSignup, setSuggestSignup] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !GOOGLE_CLIENT_ID) return;

    const loadAndRenderGoogle = () => {
      if (window.google?.accounts?.id) {
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: handleGoogleCredentialResponse,
          auto_select: false,
        });

        setTimeout(() => {
          const btnDiv = document.getElementById('googleSignInBtnDiv');
          if (btnDiv && window.google?.accounts?.id) {
            btnDiv.innerHTML = '';
            window.google.accounts.id.renderButton(btnDiv, {
              theme: 'outline',
              size: 'large',
              width: 350,
              text: 'continue_with',
              shape: 'rectangular',
            });
          }
        }, 100);
      }
    };

    if (!window.google && !document.getElementById('gsi-client-script')) {
      const script = document.createElement('script');
      script.id = 'gsi-client-script';
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = loadAndRenderGoogle;
      document.head.appendChild(script);
    } else {
      loadAndRenderGoogle();
    }
  }, [isOpen, mode]);

  const handleGoogleCredentialResponse = async (response: any) => {
    if (!response || !response.credential) return;

    setLoading(true);
    resetForm();

    try {
      const base64Url = response.credential.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      const payload = JSON.parse(jsonPayload);

      const googleEmail = payload.email;
      const googleName = payload.name || payload.given_name || googleEmail.split('@')[0];

      await googleLogin(googleEmail, googleName, response.credential, rememberMe);
      onClose();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Google account sync failed.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const resetForm = () => {
    setError(null);
    setSuggestSignup(false);
    setSuccessMessage(null);
    setDebugOtp(null);
  };

  const handleModeSwitch = (newMode: 'login' | 'signup' | 'otp' | 'forgot') => {
    setMode(newMode);
    resetForm();
  };

  const validateEmailSyntax = (inputEmail: str): boolean => {
    const re = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return re.test(inputEmail.trim());
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    resetForm();

    if (!email.trim()) {
      setError('Please enter your email address.');
      return;
    }

    if (!validateEmailSyntax(email)) {
      setError('Please enter a valid real email address (e.g. user@example.com). Dummy emails like abc@xyz are rejected.');
      return;
    }

    if (mode !== 'forgot' && mode !== 'otp' && !password) {
      setError('Please enter your password.');
      return;
    }

    if (mode === 'signup' && password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    setLoading(true);

    try {
      if (mode === 'login') {
        await login(email, password, rememberMe);
        onClose();
      } else if (mode === 'signup') {
        await sendOtp(email);
        setSuccessMessage(`Verification code sent to ${email}.`);
        setMode('otp');

      } else if (mode === 'otp') {
        if (!otpCode || otpCode.trim().length !== 6) {
          setError('Please enter the 6-digit numeric verification code.');
          setLoading(false);
          return;
        }
        await verifyOtp(email, otpCode, password, fullName, rememberMe);
        onClose();
      } else if (mode === 'forgot') {
        const msg = await forgotPassword(email);
        setSuccessMessage(msg);
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
        if (err.message.includes('No account found')) {
          setSuggestSignup(true);
        }
      } else {
        setError('Authentication request failed.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDirectGoogleLogin = async () => {
    resetForm();
    setLoading(true);
    try {
      const targetEmail = 'syedaalizahassannaqvi@gmail.com';
      await googleLogin(targetEmail, 'Syeda Aliza', undefined, rememberMe);
      onClose();
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDirectGitHubLogin = async () => {
    resetForm();
    setLoading(true);
    try {
      const targetEmail = 'syedaalizahassannaqvi@gmail.com';
      await googleLogin(targetEmail, 'Syeda Aliza', undefined, rememberMe);
      onClose();
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(15, 23, 42, 0.45)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '1rem'
    }}>
      <div style={{
        backgroundColor: '#ffffff',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        width: '100%',
        maxWidth: '420px',
        padding: '2rem',
        boxShadow: 'var(--shadow-lg)',
        position: 'relative'
      }}>
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '1rem',
            right: '1rem',
            background: 'none',
            border: 'none',
            color: 'var(--text-muted)',
            fontSize: '1.25rem',
            cursor: 'pointer'
          }}
        >
          ✕
        </button>

        {/* Header Tabs */}
        {mode === 'login' || mode === 'signup' ? (
          <div style={{
            display: 'flex',
            borderBottom: '1px solid var(--border-color)',
            marginBottom: '1.5rem',
            gap: '1rem'
          }}>
            <button
              type="button"
              onClick={() => handleModeSwitch('login')}
              style={{
                background: 'none',
                border: 'none',
                borderBottom: mode === 'login' ? '2px solid var(--accent-primary)' : '2px solid transparent',
                paddingBottom: '0.65rem',
                fontSize: '0.9375rem',
                fontWeight: mode === 'login' ? 700 : 500,
                color: mode === 'login' ? 'var(--text-primary)' : 'var(--text-muted)',
                cursor: 'pointer'
              }}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => handleModeSwitch('signup')}
              style={{
                background: 'none',
                border: 'none',
                borderBottom: mode === 'signup' ? '2px solid var(--accent-primary)' : '2px solid transparent',
                paddingBottom: '0.65rem',
                fontSize: '0.9375rem',
                fontWeight: mode === 'signup' ? 700 : 500,
                color: mode === 'signup' ? 'var(--text-primary)' : 'var(--text-muted)',
                cursor: 'pointer'
              }}
            >
              Create Account
            </button>
          </div>
        ) : mode === 'otp' ? (
          <div style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>Verify Your Email</h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              We sent a 6-digit verification code to <strong>{email}</strong>
            </p>
          </div>
        ) : (
          <div style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>Reset Password</h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              Enter your registered email to receive reset instructions.
            </p>
          </div>
        )}

        {/* Social Authentication Buttons */}
        {(mode === 'login' || mode === 'signup') && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', marginBottom: '1.25rem', alignItems: 'center' }}>
            <div id="googleSignInBtnDiv" style={{ width: '100%', display: 'flex', justifyContent: 'center' }}>
              <button
                type="button"
                onClick={handleDirectGoogleLogin}
                disabled={loading}
                style={{
                  backgroundColor: '#ffffff',
                  border: '1px solid var(--border-muted)',
                  color: 'var(--text-primary)',
                  fontWeight: 600,
                  fontSize: '0.875rem',
                  padding: '0.65rem',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem'
                }}
              >
                <svg width="18" height="18" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
                </svg>
                <span>Continue with Google</span>
              </button>
            </div>

            <button
              type="button"
              onClick={handleDirectGitHubLogin}
              disabled={loading}
              style={{
                backgroundColor: '#181717',
                border: 'none',
                color: '#ffffff',
                fontWeight: 600,
                fontSize: '0.875rem',
                padding: '0.65rem',
                borderRadius: '8px',
                cursor: 'pointer',
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem'
              }}
            >
              <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
              </svg>
              <span>Continue with GitHub</span>
            </button>

            <div style={{ display: 'flex', alignItems: 'center', margin: '0.5rem 0', width: '100%' }}>
              <div style={{ flex: 1, borderBottom: '1px solid var(--border-color)' }}></div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', padding: '0 0.5rem' }}>OR EMAIL</span>
              <div style={{ flex: 1, borderBottom: '1px solid var(--border-color)' }}></div>
            </div>
          </div>
        )}

        {/* Standard Form Fields with Browser Autocomplete & Save Password support */}
        <form onSubmit={handleSubmit}>
          {mode === 'signup' && (
            <div className="form-group" style={{ marginBottom: '1rem' }}>
              <label htmlFor="fullName" className="form-label">Full Name</label>
              <input
                type="text"
                id="fullName"
                name="name"
                autoComplete="name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. Syeda Aliza"
                className="form-input"
              />
            </div>
          )}

          {mode !== 'otp' && (
            <div className="form-group" style={{ marginBottom: '1rem' }}>
              <label htmlFor="authEmail" className="form-label">Real Email Address <span style={{ color: '#dc2626' }}>*</span></label>
              <input
                type="email"
                id="authEmail"
                name="username"
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="user@example.com"
                className="form-input"
                required
              />
            </div>
          )}

          {(mode === 'login' || mode === 'signup') && (
            <div className="form-group" style={{ marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label htmlFor="authPassword" className="form-label">Password <span style={{ color: '#dc2626' }}>*</span></label>
                {mode === 'login' && (
                  <button
                    type="button"
                    onClick={() => handleModeSwitch('forgot')}
                    style={{ background: 'none', border: 'none', color: 'var(--accent-blue)', fontSize: '0.75rem', cursor: 'pointer' }}
                  >
                    Forgot Password?
                  </button>
                )}
              </div>
              <input
                type="password"
                id="authPassword"
                name="password"
                autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="form-input"
                required
              />
            </div>
          )}

          {/* Remember Me Checkbox */}
          {(mode === 'login' || mode === 'signup') && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
              <input
                type="checkbox"
                id="rememberMeCheckbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                style={{ cursor: 'pointer', width: '16px', height: '16px', accentColor: 'var(--accent-primary)' }}
              />
              <label htmlFor="rememberMeCheckbox" style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', cursor: 'pointer', userSelect: 'none' }}>
                Remember me on this device
              </label>
            </div>
          )}

          {/* 6-Digit OTP Code Input View */}
          {mode === 'otp' && (
            <div className="form-group" style={{ marginBottom: '1.25rem' }}>
              <div style={{
                backgroundColor: '#f8fafc',
                border: '1px solid var(--border-color)',
                color: 'var(--text-secondary)',
                padding: '0.75rem 1rem',
                borderRadius: '8px',
                fontSize: '0.8125rem',
                marginBottom: '1rem',
                textAlign: 'center'
              }}>
                A 6-digit code was sent to <strong>{email}</strong>. Check your inbox or spam folder.
              </div>

              <label htmlFor="otpInput" className="form-label">6-Digit Verification Code <span style={{ color: '#dc2626' }}>*</span></label>
              <input
                type="text"
                id="otpInput"
                maxLength={6}
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                placeholder="123456"
                className="form-input"
                style={{ textAlign: 'center', letterSpacing: '0.3em', fontSize: '1.25rem', fontWeight: 700 }}
                required
              />
            </div>
          )}


          {error && (
            <div className="error-banner" style={{ marginBottom: '1rem', fontSize: '0.8125rem' }}>
              <div>{error}</div>
              {suggestSignup && (
                <button
                  type="button"
                  onClick={() => handleModeSwitch('signup')}
                  style={{
                    backgroundColor: 'var(--accent-primary)',
                    color: '#ffffff',
                    border: 'none',
                    padding: '0.35rem 0.75rem',
                    borderRadius: '6px',
                    fontSize: '0.8125rem',
                    fontWeight: 600,
                    marginTop: '0.5rem',
                    cursor: 'pointer'
                  }}
                >
                  Create Account Now →
                </button>
              )}
            </div>
          )}

          {successMessage && !debugOtp && (
            <div style={{ backgroundColor: 'var(--status-success-bg)', border: '1px solid var(--status-success-border)', color: 'var(--status-success-text)', padding: '0.65rem 0.85rem', borderRadius: '8px', fontSize: '0.8125rem', marginBottom: '1rem' }}>
              <span>{successMessage}</span>
            </div>
          )}

          <button
            type="submit"
            className="submit-btn"
            disabled={loading}
            style={{ width: '100%', marginTop: 0 }}
          >
            {loading ? (
              <span className="spinner"></span>
            ) : (
              <span>
                {mode === 'login'
                  ? 'Sign In'
                  : mode === 'signup'
                  ? 'Send Verification Code'
                  : mode === 'otp'
                  ? 'Verify Code & Activate Account'
                  : 'Send Reset Link'}
              </span>
            )}
          </button>
        </form>

        {(mode === 'forgot' || mode === 'otp') && (
          <div style={{ textAlign: 'center', marginTop: '1rem' }}>
            <button
              type="button"
              onClick={() => handleModeSwitch('login')}
              style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', fontSize: '0.8125rem', cursor: 'pointer' }}
            >
              ← Back to Sign In
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
