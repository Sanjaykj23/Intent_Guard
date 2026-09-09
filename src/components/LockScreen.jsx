import React from 'react';
import { Lock, ShieldCheck, ArrowRight } from 'lucide-react';

/**
 * LockScreen — Locked State Component
 * Displayed when session is manually locked.
 */
export default function LockScreen({ onUnlockRequest }) {
  return (
    <div className="lock-container fade-in">
      <div className="lock-card slide-up">
        <div style={{ display: 'inline-flex', padding: '1rem', background: 'rgba(99, 102, 241, 0.15)', borderRadius: '50%', marginBottom: '1.25rem', color: '#818cf8' }}>
          <Lock size={36} />
        </div>

        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#ffffff', marginBottom: '0.5rem' }}>
          Intent Guard Locked
        </h2>

        <p className="auth-tagline" style={{ marginBottom: '2rem' }}>
          Your authorized session is protected.
        </p>

        <button onClick={onUnlockRequest} className="btn-primary">
          <Lock size={18} />
          <span>Unlock Intent Guard</span>
          <ArrowRight size={16} />
        </button>

        <div className="security-badge-dark">
          <ShieldCheck size={16} />
          <span>Payment credentials are stored outside the AI boundary.</span>
        </div>
      </div>
    </div>
  );
}
