import React, { useState, useEffect } from 'react';
import { Zap, RefreshCw, CheckCircle2, XCircle } from 'lucide-react';
import { fetchSimulatedUPIDelegation, revokeSimulatedUPIDelegation, createSimulatedUPIDelegation, resetDemoData } from '../services/api';

/**
 * UPI Circle Status Dashboard Component
 * Displays simulated delegation limits, spent amount, and remaining quota.
 * Stores & isolates delegation status strictly per authenticated user.
 */
export default function UPICircleDashboard({ onOpenSetup, user }) {
  const [delegation, setDelegation] = useState(null);
  const [loading, setLoading] = useState(true);

  const getActiveUserId = () => {
    if (user?.user_id) return user.user_id;
    const saved = localStorage.getItem('intentguard_user');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed?.user_id) return parsed.user_id;
      } catch (e) {}
    }
    return "USER_DEFAULT_001";
  };

  const loadData = async () => {
    setLoading(true);
    const activeUserId = getActiveUserId();
    const delData = await fetchSimulatedUPIDelegation(activeUserId);
    setDelegation(delData);
    setLoading(false);
  };

  useEffect(() => {
    loadData();
    const handleUpdate = () => loadData();
    if (typeof window !== 'undefined') {
      window.addEventListener('upi_circle_updated', handleUpdate);
    }
    return () => {
      if (typeof window !== 'undefined') {
        window.removeEventListener('upi_circle_updated', handleUpdate);
      }
    };
  }, [user]);

  const handleRevoke = async () => {
    const activeUserId = getActiveUserId();
    await revokeSimulatedUPIDelegation(activeUserId);
    await loadData();
  };

  const handleConnect = async () => {
    if (onOpenSetup) {
      onOpenSetup();
    } else {
      const activeUserId = getActiveUserId();
      await createSimulatedUPIDelegation(15000, 5000, activeUserId);
      await loadData();
    }
  };

  const handleReset = async () => {
    const activeUserId = getActiveUserId();
    await resetDemoData(activeUserId);
    await loadData();
  };

  if (loading || !delegation) {
    return null;
  }

  const isConnected = delegation.has_delegation && delegation.status === 'ACTIVE';

  return (
    <div style={{
      background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
      color: '#f8fafc',
      padding: '1.25rem 1.5rem',
      borderRadius: '1rem',
      margin: '1rem 0',
      boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.3)',
      border: '1px solid rgba(255, 255, 255, 0.1)'
    }}>
      {/* Header Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            background: isConnected ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
            padding: '0.5rem',
            borderRadius: '0.75rem',
            color: isConnected ? '#34d399' : '#f87171',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            {isConnected ? <CheckCircle2 size={22} /> : <XCircle size={22} />}
          </div>
          <div>
            <div style={{ fontSize: '1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span>UPI Circle</span>
              <span style={{
                fontSize: '0.7rem',
                background: isConnected ? '#059669' : '#dc2626',
                color: '#ffffff',
                padding: '0.15rem 0.5rem',
                borderRadius: '1rem',
                fontWeight: 600
              }}>
                {isConnected ? 'Connected ✓' : 'Disconnected'}
              </span>
            </div>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
              AI Payment Agent (Delegated Authority)
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {isConnected ? (
            <button
              onClick={handleRevoke}
              style={{
                padding: '0.4rem 0.85rem',
                background: 'rgba(239, 68, 68, 0.2)',
                color: '#f87171',
                border: '1px solid rgba(239, 68, 68, 0.4)',
                borderRadius: '0.5rem',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              Disable
            </button>
          ) : (
            <button
              onClick={handleConnect}
              style={{
                padding: '0.4rem 0.85rem',
                background: '#2563eb',
                color: '#ffffff',
                border: 'none',
                borderRadius: '0.5rem',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              Connect UPI
            </button>
          )}

          <button
            onClick={handleReset}
            title="Development-Only Hackathon Demo Reset"
            style={{
              padding: '0.4rem 0.65rem',
              background: 'rgba(255, 255, 255, 0.1)',
              color: '#cbd5e1',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: '0.5rem',
              fontSize: '0.75rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.25rem'
            }}
          >
            <RefreshCw size={12} />
            <span>Reset Demo</span>
          </button>
        </div>
      </div>

      {/* Metrics Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
        gap: '0.75rem',
        marginTop: '0.75rem'
      }}>
        <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '0.75rem', borderRadius: '0.75rem' }}>
          <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Monthly Limit</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#38bdf8', marginTop: '0.2rem' }}>
            ₹{(delegation.monthly_limit || 15000).toLocaleString('en-IN')}
          </div>
        </div>

        <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '0.75rem', borderRadius: '0.75rem' }}>
          <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Used This Month</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f43f5e', marginTop: '0.2rem' }}>
            ₹{(delegation.spent_this_month || 0).toLocaleString('en-IN')}
          </div>
        </div>

        <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '0.75rem', borderRadius: '0.75rem' }}>
          <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Remaining Quota</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#34d399', marginTop: '0.2rem' }}>
            ₹{(delegation.remaining || 15000).toLocaleString('en-IN')}
          </div>
        </div>

        <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '0.75rem', borderRadius: '0.75rem' }}>
          <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Per Transaction</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fbbf24', marginTop: '0.2rem' }}>
            ₹{(delegation.transaction_limit || 5000).toLocaleString('en-IN')}
          </div>
        </div>
      </div>
    </div>
  );
}
