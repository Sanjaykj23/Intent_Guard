import React, { useState } from 'react';
import { X, ShieldCheck, CheckCircle2, AlertCircle, ArrowRight, Zap, Lock, CreditCard, Eye, EyeOff, KeyRound } from 'lucide-react';
import { setupUPICircleMandate } from '../services/api';

export default function UPICircleSetupModal({ isOpen, onClose, user, onMandateCreated }) {
  const [primaryVpa, setPrimaryVpa] = useState(user?.email ? `${user.email.split('@')[0]}@upi` : 'sanjay@okicici');
  const [perTxnLimit, setPerTxnLimit] = useState('5000');
  const [monthlyLimit, setMonthlyLimit] = useState('15000');
  const [upiPin, setUpiPin] = useState('');
  const [showPin, setShowPin] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!primaryVpa.trim() || !primaryVpa.includes('@')) {
      setError('Please enter a valid Primary Bank UPI VPA (e.g. user@upi).');
      return;
    }

    if (!upiPin || (upiPin.length !== 4 && upiPin.length !== 6)) {
      setError('Please enter a valid 4 or 6-digit UPI PIN to authorize mandate setup.');
      return;
    }

    const perTxnPaise = parseInt(perTxnLimit) * 100;
    const monthlyPaise = parseInt(monthlyLimit) * 100;

    if (perTxnPaise > 500000) {
      setError('NPCI UPI Circle full delegation hard cap is ₹5,000 per transaction.');
      return;
    }

    if (monthlyPaise > 1500000) {
      setError('NPCI UPI Circle monthly cumulative hard cap is ₹15,000.');
      return;
    }

    setIsLoading(true);

    try {
      const res = await setupUPICircleMandate(primaryVpa, perTxnPaise, monthlyPaise, user?.token, upiPin, user?.user_id);
      if (res.success || res.mandate_id) {
        onMandateCreated(res);
        onClose();
      } else {
        setError(res.message || 'Failed to setup UPI Circle mandate.');
      }
    } catch (err) {
      setError('An error occurred during setup. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="modal-overlay fade-in" style={{
      position: 'fixed',
      inset: 0,
      backgroundColor: 'rgba(15, 23, 42, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '1rem'
    }}>
      <div className="modal-container slide-up" style={{
        background: '#ffffff',
        borderRadius: '1.25rem',
        maxWidth: '500px',
        width: '100%',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        overflow: 'hidden',
        border: '1px solid rgba(226, 232, 240, 0.8)'
      }}>
        {/* Header */}
        <div style={{
          padding: '1.25rem 1.5rem',
          borderBottom: '1px solid #f1f5f9',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'linear-gradient(to right, #eff6ff, #ffffff)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
            <div style={{
              width: '38px',
              height: '38px',
              borderRadius: '0.625rem',
              background: 'linear-gradient(135deg, #10b981, #059669)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff'
            }}>
              <Zap size={22} />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 700, color: '#0f172a' }}>
                Enable UPI Circle Delegation
              </h3>
              <p style={{ margin: 0, fontSize: '0.75rem', color: '#64748b' }}>
                NPCI Autonomous PIN-Less Payment Rail
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '0.25rem'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} style={{ padding: '1.5rem' }}>
          {error && (
            <div style={{
              marginBottom: '1rem',
              padding: '0.75rem',
              background: '#fef2f2',
              border: '1px solid #fecaca',
              borderRadius: '0.5rem',
              color: '#dc2626',
              fontSize: '0.8125rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          {/* Zero-Trust Compliance Callout */}
          <div style={{
            marginBottom: '1.25rem',
            padding: '0.875rem',
            background: 'rgba(16, 185, 129, 0.08)',
            border: '1px solid rgba(16, 185, 129, 0.25)',
            borderRadius: '0.625rem',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '0.625rem'
          }}>
            <ShieldCheck size={20} style={{ color: '#059669', flexShrink: 0, marginTop: '2px' }} />
            <div style={{ fontSize: '0.75rem', color: '#065f46', lineHeight: 1.4 }}>
              <strong>STRICT ZERO-TRUST SECURITY:</strong> We only register your bank VPA and delegation caps. <strong>Raw credit/debit card numbers and 4/6-digit UPI PINs are NEVER stored.</strong>
            </div>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#334155', marginBottom: '0.375rem' }}>
              Primary Bank UPI VPA Handle
            </label>
            <input
              type="text"
              value={primaryVpa}
              onChange={(e) => setPrimaryVpa(e.target.value)}
              placeholder="sanjay@okicici or user@upi"
              style={{
                width: '100%',
                padding: '0.625rem 0.75rem',
                border: '1px solid #cbd5e1',
                borderRadius: '0.5rem',
                fontSize: '0.875rem',
                outline: 'none'
              }}
              required
            />
            <span style={{ fontSize: '0.70rem', color: '#64748b', marginTop: '0.25rem', display: 'block' }}>
              Primary user account VPA that approves secondary agent delegation.
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '1.25rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#334155', marginBottom: '0.375rem' }}>
                Per-Txn Limit (Max ₹5,000)
              </label>
              <div style={{ position: 'relative' }}>
                <span style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', fontWeight: 600, color: '#64748b' }}>₹</span>
                <input
                  type="number"
                  max="5000"
                  value={perTxnLimit}
                  onChange={(e) => setPerTxnLimit(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.625rem 0.75rem 0.625rem 2rem',
                    border: '1px solid #cbd5e1',
                    borderRadius: '0.5rem',
                    fontSize: '0.875rem',
                    outline: 'none'
                  }}
                  required
                />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#334155', marginBottom: '0.375rem' }}>
                Monthly Cap (Max ₹15,000)
              </label>
              <div style={{ position: 'relative' }}>
                <span style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', fontWeight: 600, color: '#64748b' }}>₹</span>
                <input
                  type="number"
                  max="15000"
                  value={monthlyLimit}
                  onChange={(e) => setMonthlyLimit(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.625rem 0.75rem 0.625rem 2rem',
                    border: '1px solid #cbd5e1',
                    borderRadius: '0.5rem',
                    fontSize: '0.875rem',
                    outline: 'none'
                  }}
                  required
                />
              </div>
            </div>
          </div>

          {/* Primary Bank 4/6-Digit UPI PIN Field */}
          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#334155', marginBottom: '0.375rem' }}>
              Primary Bank 4/6-Digit UPI PIN (Mandate Authorization)
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type={showPin ? "text" : "password"}
                maxLength={6}
                value={upiPin}
                onChange={(e) => setUpiPin(e.target.value.replace(/\D/g, ''))}
                placeholder="Enter 4 or 6 digit UPI PIN..."
                style={{
                  width: '100%',
                  padding: '0.625rem 2.5rem 0.625rem 0.75rem',
                  border: '1px solid #cbd5e1',
                  borderRadius: '0.5rem',
                  fontSize: '0.875rem',
                  outline: 'none',
                  letterSpacing: '0.15em'
                }}
                required
              />
              <button
                type="button"
                onClick={() => setShowPin(!showPin)}
                style={{
                  position: 'absolute',
                  right: '0.75rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  color: '#64748b',
                  cursor: 'pointer'
                }}
              >
                {showPin ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            <span style={{ fontSize: '0.70rem', color: '#64748b', marginTop: '0.25rem', display: 'block' }}>
              Required by NPCI to authorize delegation mandate setup. The PIN is transmitted for one-time activation and is NEVER stored.
            </span>
          </div>

          <div style={{
            padding: '0.75rem',
            background: '#f8fafc',
            border: '1px dashed #cbd5e1',
            borderRadius: '0.5rem',
            fontSize: '0.75rem',
            color: '#475569',
            marginBottom: '1.25rem'
          }}>
            <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>NPCI Guardrails Enforced:</div>
            • 24-hour cooling-off autonomous cap: ₹2,000 max.<br />
            • Amounts &gt; ₹5,000 trigger Step-Up UPI PIN requirement automatically.
          </div>

          <button
            type="submit"
            disabled={isLoading}
            style={{
              width: '100%',
              padding: '0.75rem',
              background: 'linear-gradient(135deg, #10b981, #059669)',
              color: '#ffffff',
              border: 'none',
              borderRadius: '0.5rem',
              fontWeight: 600,
              fontSize: '0.875rem',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              boxShadow: '0 4px 6px -1px rgba(16, 185, 129, 0.3)'
            }}
          >
            {isLoading ? (
              <span>Establishing Mandate...</span>
            ) : (
              <>
                <CheckCircle2 size={18} />
                <span>Activate UPI Circle Delegation</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
