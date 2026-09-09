import React, { useState } from 'react';
import { Sparkles, Lock, Eye, EyeOff, ShieldCheck, AlertCircle, ArrowRight } from 'lucide-react';
import { authenticateUser } from '../services/api';

/**
 * AuthScreen — Initial Authentication Screen
 * Demo authentication wrapper using mock API service.
 * Demo password: intent123
 */
export default function AuthScreen({ onAuthenticate }) {
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!password.trim()) return;

    setIsLoading(true);
    setError('');

    try {
      // Call mock authentication in api.js
      const result = await authenticateUser(password);
      if (result.success) {
        onAuthenticate(result);
      } else {
        setError(result.message || 'Invalid password. Try "intent123" for demo access.');
      }
    } catch (err) {
      setError('An unexpected error occurred. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container fade-in">
      <div className="auth-card slide-up">
        {/* Brand Logo & Icon */}
        <div className="auth-logo">
          <Sparkles className="sparkle-icon" size={28} />
          <span>Intent Guard</span>
        </div>
        <p className="auth-tagline">Secure Agent Payment Access</p>

        {/* Form */}
        <form onSubmit={handleSubmit} className="auth-form">
          {error && (
            <div className="error-banner">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="input-label" htmlFor="auth-password">
              Authorization Password
            </label>
            <div className="password-field-wrapper">
              <input
                id="auth-password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password to unlock..."
                className="password-input"
                autoFocus
                disabled={isLoading}
              />
              <button
                type="button"
                className="toggle-password-btn"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={isLoading || !password.trim()}
          >
            {isLoading ? (
              <>
                <div className="step-spinner" />
                <span>Verifying Access...</span>
              </>
            ) : (
              <>
                <Lock size={18} />
                <span>Unlock Intent Guard</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>

        {/* Security Concept Disclaimer */}
        <div className="security-badge-dark">
          <ShieldCheck size={16} />
          <span>Your payment credentials are never exposed to the AI.</span>
        </div>
      </div>
    </div>
  );
}
