import React from 'react';
import { Check, ShoppingBag, ArrowRight, PackageCheck, ShieldCheck } from 'lucide-react';

/**
 * SuccessMessage Component
 * Displays transaction success receipt without wallet or bank balance information.
 */
export default function SuccessMessage({ transaction, onContinueShopping }) {
  if (!transaction) return null;

  return (
    <div className="success-card fade-in">
      <div className="success-icon-badge">
        <Check size={32} strokeWidth={3} />
      </div>

      <h2 className="success-title">Transaction Successful</h2>
      <p style={{ color: '#047857', fontSize: '0.9375rem', marginTop: '-0.5rem' }}>
        Your request has been securely processed.
      </p>

      {/* Transaction Details Box */}
      <div className="success-details-box">
        <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.5rem' }}>
          <span style={{ color: 'var(--text-muted)' }}>Transaction ID:</span>
          <strong style={{ fontFamily: 'monospace', color: 'var(--primary-600)' }}>
            {transaction.transactionId}
          </strong>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: 'var(--text-muted)' }}>Authorized Amount:</span>
          <strong style={{ color: 'var(--text-main)' }}>
            {transaction.formattedAmount || `₹${((transaction.amountPaidPaise || 0) / 100).toLocaleString('en-IN')}`}
          </strong>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: 'var(--text-muted)' }}>Status:</span>
          <strong style={{ color: 'var(--emerald-600)' }}>
            Authorized & Executed
          </strong>
        </div>
      </div>

      {/* Core Security Reassurance */}
      <div style={{ fontSize: '0.8125rem', color: '#047857', display: 'flex', alignItems: 'center', gap: '0.375rem', fontWeight: 500 }}>
        <ShieldCheck size={16} />
        <span>🔐 Payment credentials were not exposed to the AI.</span>
      </div>

      {/* Action Buttons */}
      <div className="success-actions">
        <button
          onClick={() => alert(`Order details for ${transaction.transactionId}`)}
          className="btn-secondary"
          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
        >
          <PackageCheck size={16} />
          <span>View Order</span>
        </button>

        <button
          onClick={onContinueShopping}
          className="btn-primary"
          style={{ width: 'auto' }}
        >
          <ShoppingBag size={16} />
          <span>Continue</span>
          <ArrowRight size={16} />
        </button>
      </div>
    </div>
  );
}
