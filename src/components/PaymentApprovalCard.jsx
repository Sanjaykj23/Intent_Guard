import React, { useState } from 'react';
import { AlertTriangle, CheckCircle, XCircle, ShieldAlert } from 'lucide-react';
import { initiatePaymentDecision } from '../services/api';

/**
 * Payment Approval Card Component
 * Displayed in Chatbot when Payment Decision Engine returns REQUIRES_USER_APPROVAL.
 * Requires explicit user action before simulated payment execution.
 */
export default function PaymentApprovalCard({ decisionData, onResolved }) {
  const [status, setStatus] = useState('PENDING'); // PENDING | SUCCESS | REJECTED | EXECUTING
  const [loading, setLoading] = useState(false);
  const [txnResult, setTxnResult] = useState(null);

  const {
    transaction_id = "TXN_MOCK_APPROVAL",
    merchant = "Demo Merchant",
    amount = 4500,
    category = "SHOPPING",
    reason = "High-risk transaction requires user approval",
    risk_score = 0.75
  } = decisionData || {};

  const handleApprove = async () => {
    setLoading(true);
    setStatus('EXECUTING');
    const res = await initiatePaymentDecision(transaction_id, 'APPROVE', decisionData?.user_id);
    setLoading(false);
    if (res.status === 'SUCCESS') {
      setStatus('SUCCESS');
      setTxnResult(res);
      if (onResolved) onResolved({ status: 'SUCCESS', result: res });
    } else {
      setStatus('REJECTED');
      if (onResolved) onResolved({ status: 'FAILED', result: res });
    }
  };

  const handleReject = async () => {
    setLoading(true);
    const res = await initiatePaymentDecision(transaction_id, 'REJECT', decisionData?.user_id);
    setLoading(false);
    setStatus('REJECTED');
    if (onResolved) onResolved({ status: 'CANCELLED', result: res });
  };

  if (status === 'SUCCESS') {
    return (
      <div style={{
        background: '#ecfdf5',
        border: '1px solid #10b981',
        borderRadius: '0.75rem',
        padding: '1rem 1.25rem',
        margin: '0.75rem 0',
        color: '#065f46'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, fontSize: '1rem', color: '#047857' }}>
          <CheckCircle size={20} />
          <span>Payment Approved & Executed</span>
        </div>
        <div style={{ fontSize: '0.85rem', marginTop: '0.5rem', color: '#047857' }}>
          <div><strong>Merchant:</strong> {merchant}</div>
          <div><strong>Amount Paid:</strong> ₹{amount.toLocaleString('en-IN')}</div>
          <div><strong>Transaction ID:</strong> {transaction_id}</div>
          <div><strong>Status:</strong> SUCCESS</div>
        </div>
      </div>
    );
  }

  if (status === 'REJECTED') {
    return (
      <div style={{
        background: '#fef2f2',
        border: '1px solid #ef4444',
        borderRadius: '0.75rem',
        padding: '1rem 1.25rem',
        margin: '0.75rem 0',
        color: '#991b1b'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, fontSize: '1rem', color: '#b91c1c' }}>
          <XCircle size={20} />
          <span>Payment Rejected by User</span>
        </div>
        <div style={{ fontSize: '0.85rem', marginTop: '0.35rem', color: '#7f1d1d' }}>
          Transaction {transaction_id} was cancelled. No funds were debited.
        </div>
      </div>
    );
  }

  return (
    <div style={{
      background: '#fffbe8',
      border: '2px solid #f59e0b',
      borderRadius: '0.85rem',
      padding: '1.25rem',
      margin: '0.85rem 0',
      boxShadow: '0 4px 15px -2px rgba(245, 158, 11, 0.15)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, fontSize: '1.05rem', color: '#b45309' }}>
        <ShieldAlert size={22} style={{ color: '#d97706' }} />
        <span>Payment Approval Required</span>
      </div>

      <div style={{ fontSize: '0.875rem', marginTop: '0.75rem', color: '#1e293b', lineHeight: 1.6 }}>
        <div><strong>Merchant:</strong> {merchant}</div>
        <div><strong>Amount:</strong> ₹{amount.toLocaleString('en-IN')}</div>
        <div><strong>Category:</strong> {category}</div>
        <div><strong>Risk Score:</strong> <span style={{ color: '#dc2626', fontWeight: 700 }}>{risk_score} (HIGH)</span></div>
        <div style={{ marginTop: '0.35rem', fontStyle: 'italic', color: '#64748b' }}>
          <strong>Reason:</strong> {reason}
        </div>
      </div>

      <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
        <button
          onClick={handleApprove}
          disabled={loading}
          style={{
            flex: 1,
            padding: '0.6rem 1rem',
            background: '#059669',
            color: '#ffffff',
            border: 'none',
            borderRadius: '0.5rem',
            fontWeight: 600,
            fontSize: '0.875rem',
            cursor: loading ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.35rem'
          }}
        >
          {loading ? 'Processing...' : 'Approve Payment'}
        </button>

        <button
          onClick={handleReject}
          disabled={loading}
          style={{
            flex: 1,
            padding: '0.6rem 1rem',
            background: '#dc2626',
            color: '#ffffff',
            border: 'none',
            borderRadius: '0.5rem',
            fontWeight: 600,
            fontSize: '0.875rem',
            cursor: loading ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.35rem'
          }}
        >
          Reject Payment
        </button>
      </div>
    </div>
  );
}
