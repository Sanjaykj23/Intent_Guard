import React, { useState } from 'react';
import { Sparkles, Lock, Eye, EyeOff, ShieldCheck, AlertCircle, ArrowRight, User, Mail, CreditCard } from 'lucide-react';
import { authenticateUser } from '../services/api';

/**
 * AuthScreen — User Account Registration & Razorpay Token Setup Screen
 * Tagline: Ask. Search. Decide. Pay Safely.
 */
export default function AuthScreen({ onAuthenticate }) {
  const [name, setName] = useState('Sanjay Kumar');
  const [email, setEmail] = useState('sanjay@intentguard.ai');
  const [password, setPassword] = useState('intent123');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!password.trim() || !email.trim()) return;

    setIsLoading(true);
    setError('');

    try {
      const result = await authenticateUser(password, email, name);
      if (result.success) {
        onAuthenticate(result);
      } else {
        setError(result.message || 'Authentication failed. Please try again.');
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
          <span>IntentGuard AI</span>
        </div>
        <p className="auth-tagline">Ask. Search. Decide. Pay Safely.</p>

        {/* Form */}
        <form onSubmit={handleSubmit} className="auth-form">
          {error && (
            <div className="error-banner">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="input-label" htmlFor="auth-name">Full Name</label>
            <div className="password-field-wrapper">
              <input
                id="auth-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter your full name..."
                className="password-input"
                disabled={isLoading}
              />
            </div>
          </div>

          <div style={{ marginTop: '0.75rem' }}>
            <label className="input-label" htmlFor="auth-email">Email Address</label>
            <div className="password-field-wrapper">
              <input
                id="auth-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter email address..."
                className="password-input"
                disabled={isLoading}
              />
            </div>
          </div>

          <div style={{ marginTop: '0.75rem' }}>
            <label className="input-label" htmlFor="auth-password">Password / Security Pin</label>
            <div className="password-field-wrapper">
              <input
                id="auth-password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password..."
                className="password-input"
                disabled={isLoading}
              />
              <button
                type="button"
                className="toggle-password-btn"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          {/* Razorpay Token Vault Badge */}
          <div className="razorpay-vault-badge" style={{
            margin: '0.75rem 0',
            padding: '0.625rem 0.75rem',
            background: 'rgba(59, 130, 246, 0.08)',
            border: '1px solid rgba(59, 130, 246, 0.2)',
            borderRadius: '0.5rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontSize: '0.75rem',
            color: 'var(--primary-600, #3b82f6)'
          }}>
            <CreditCard size={16} />
            <span>Razorpay Mandate Token Hashed & Secured (SHA-256)</span>
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={isLoading || !password.trim()}
          >
            {isLoading ? (
              <>
                <div className="step-spinner" />
                <span>Securing Access & Razorpay Token...</span>
              </>
            ) : (
              <>
                <Lock size={18} />
                <span>Enter IntentGuard Command Center</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>

        {/* Security Disclaimer */}
        <div className="security-badge-dark">
          <ShieldCheck size={16} />
          <span>The LLM never accesses raw bank credentials or UPI PINs.</span>
        </div>
      </div>
    </div>
  );
}
