import React, { useState } from 'react';
import { Sparkles, Lock, Eye, EyeOff, ShieldCheck, AlertCircle, ArrowRight, User, Mail, Phone, MapPin, UserPlus, LogIn } from 'lucide-react';
import { registerUser, loginUser } from '../services/api';

/**
 * AuthScreen — Main User Authentication & Registration Page
 * Allows creating a new user account (Name, Email, E.164 Mobile, Address, Password)
 * or logging into an existing account via FastAPI backend.
 */
export default function AuthScreen({ onAuthenticate }) {
  const [isLoginTab, setIsLoginTab] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!email.trim() || !password.trim()) {
      setError('Email and password are required.');
      return;
    }

    if (!isLoginTab) {
      if (!name.trim() || !phone.trim() || !address.trim()) {
        setError('Please fill in all details (Full Name, Mobile Number, Delivery Address).');
        return;
      }
      // E.164 format validation: starts with +, 8-15 digits total
      const e164Regex = /^\+[1-9]\d{7,14}$/;
      if (!e164Regex.test(phone.trim())) {
        setError('Mobile number must be in valid E.164 format (e.g. +919876543210).');
        return;
      }
    }

    setIsLoading(true);

    try {
      if (isLoginTab) {
        const result = await loginUser({ email: email.trim(), password: password.trim() });
        if (result.success) {
          localStorage.setItem('intentguard_user', JSON.stringify(result));
          onAuthenticate(result);
        } else {
          setError(result.message || 'Invalid email or password.');
        }
      } else {
        const result = await registerUser({
          name: name.trim(),
          email: email.trim(),
          password: password.trim(),
          phone: phone.trim(),
          address: address.trim()
        });

        if (result.success) {
          localStorage.setItem('intentguard_user', JSON.stringify(result));
          onAuthenticate(result);
        } else {
          setError(result.message || 'Registration failed. Please check your details.');
        }
      }
    } catch (err) {
      setError('An unexpected connection error occurred. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container fade-in" style={{ padding: '2rem 1rem' }}>
      <div className="auth-card slide-up" style={{ maxWidth: '480px', width: '100%', padding: '2rem' }}>
        {/* Brand Logo & Icon */}
        <div className="auth-logo">
          <Sparkles className="sparkle-icon" size={28} />
          <span>IntentGuard AI</span>
        </div>
        <p className="auth-tagline">Ask. Search. Decide. Pay Safely.</p>

        {/* Tab Switcher */}
        <div style={{
          display: 'flex',
          background: 'rgba(15, 23, 42, 0.6)',
          borderRadius: '0.75rem',
          padding: '0.25rem',
          marginBottom: '1.5rem',
          border: '1px solid var(--border-dark)'
        }}>
          <button
            type="button"
            onClick={() => { setIsLoginTab(false); setError(''); }}
            style={{
              flex: 1,
              padding: '0.625rem',
              borderRadius: '0.5rem',
              background: !isLoginTab ? 'var(--primary-600)' : 'transparent',
              color: '#ffffff',
              fontWeight: 600,
              fontSize: '0.875rem',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.375rem',
              transition: 'all 0.2s ease'
            }}
          >
            <UserPlus size={16} />
            <span>Create Account</span>
          </button>

          <button
            type="button"
            onClick={() => { setIsLoginTab(true); setError(''); }}
            style={{
              flex: 1,
              padding: '0.625rem',
              borderRadius: '0.5rem',
              background: isLoginTab ? 'var(--primary-600)' : 'transparent',
              color: '#ffffff',
              fontWeight: 600,
              fontSize: '0.875rem',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.375rem',
              transition: 'all 0.2s ease'
            }}
          >
            <LogIn size={16} />
            <span>Sign In</span>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="auth-form">
          {error && (
            <div className="error-banner" style={{ marginBottom: '1rem' }}>
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          {!isLoginTab && (
            <>
              <div>
                <label className="input-label" htmlFor="auth-name">Full Name</label>
                <div className="password-field-wrapper">
                  <input
                    id="auth-name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Sanjay Kumar"
                    className="password-input"
                    disabled={isLoading}
                    required
                  />
                </div>
              </div>

              <div style={{ marginTop: '0.75rem' }}>
                <label className="input-label" htmlFor="auth-phone">Mobile Number (E.164 Format)</label>
                <div className="password-field-wrapper">
                  <input
                    id="auth-phone"
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="e.g. +919876543210"
                    className="password-input"
                    disabled={isLoading}
                    required
                  />
                </div>
              </div>

              <div style={{ marginTop: '0.75rem' }}>
                <label className="input-label" htmlFor="auth-address">Delivery Address</label>
                <div className="password-field-wrapper">
                  <input
                    id="auth-address"
                    type="text"
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    placeholder="e.g. 123 Tech Park, Bengaluru, KA"
                    className="password-input"
                    disabled={isLoading}
                    required
                  />
                </div>
              </div>
            </>
          )}

          <div style={{ marginTop: '0.75rem' }}>
            <label className="input-label" htmlFor="auth-email">Email Address</label>
            <div className="password-field-wrapper">
              <input
                id="auth-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="e.g. user@domain.com"
                className="password-input"
                disabled={isLoading}
                required
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
                placeholder="Enter account password..."
                className="password-input"
                disabled={isLoading}
                required
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

          <button
            type="submit"
            className="btn-primary"
            disabled={isLoading}
            style={{ marginTop: '1.25rem' }}
          >
            {isLoading ? (
              <>
                <div className="step-spinner" />
                <span>{isLoginTab ? 'Authenticating User...' : 'Creating Account in Database...'}</span>
              </>
            ) : (
              <>
                <Lock size={18} />
                <span>{isLoginTab ? 'Sign In to IntentGuard' : 'Register & Launch Platform'}</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>

        {/* Security Disclaimer */}
        <div className="security-badge-dark" style={{ marginTop: '1.5rem' }}>
          <ShieldCheck size={16} />
          <span>Strict Zero-Trust PCI-DSS Compliance: Credentials & UPI PINs are never stored raw.</span>
        </div>
      </div>
    </div>
  );
}
