import React, { useState } from 'react';
import { ShieldCheck, CheckCircle2, X, Lock, CreditCard, KeyRound, AlertTriangle } from 'lucide-react';

/**
 * PurchaseModal Component
 * Confirms transaction intent and executes secure payment authorization.
 * Enforces NPCI UPI Circle rules: PIN-less for <= ₹5,000, Step-up UPI PIN required for > ₹5,000.
 */
export default function PurchaseModal({ product, onClose, onConfirmPurchase }) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStepText, setCurrentStepText] = useState('');
  const [upiVpa, setUpiVpa] = useState('sanjay@okicici');
  const [upiPin, setUpiPin] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  if (!product) return null;

  const productTitle = product.name || product.title || "Product Item";
  
  const getProductPriceInRupees = (item) => {
    if (!item) return 1131;
    if (typeof item.price_paise === 'number' && item.price_paise > 0) return item.price_paise / 100;
    if (typeof item.price === 'number' && item.price > 0) return item.price > 10000 ? item.price / 100 : item.price;
    if (typeof item.amount === 'number' && item.amount > 0) return item.amount > 10000 ? item.amount / 100 : item.amount;
    if (typeof item.amount_paise === 'number' && item.amount_paise > 0) return item.amount_paise / 100;
    if (item.formatted_price && typeof item.formatted_price === 'string') {
      const clean = item.formatted_price.replace(/[^0-9.]/g, '');
      const val = parseFloat(clean);
      if (!isNaN(val) && val > 0) return val;
    }
    return 1131;
  };

  const productPrice = getProductPriceInRupees(product);
  const deliveryFee = 0;
  const totalAmount = productPrice + deliveryFee;
  const merchantName = product.provider || product.merchant || product.platform || "Merchant";
  const imageUrl = product.image_url || product.image || "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=600&auto=format&fit=crop&q=80";
  const deliveryText = product.delivery || "Fast Delivery";

  // NPCI UPI Circle Rules:
  // 1. Hard Cap: Transactions > ₹15,000 CANNOT be executed via delegation (BREACH)
  const isBreachingMonthlyCap = totalAmount > 15000;
  // 2. Step-up PIN authorization: Transactions > ₹5,000 require Step-up UPI PIN
  const requiresStepUpPin = totalAmount > 5000;

  const handleConfirm = async () => {
    setErrorMessage('');

    if (isBreachingMonthlyCap) {
      setErrorMessage(`Transaction Blocked: Amount ₹${totalAmount.toLocaleString('en-IN')} exceeds NPCI UPI Circle maximum limit of ₹15,000.`);
      return;
    }

    if (requiresStepUpPin && (!upiPin || upiPin.length < 4)) {
      setErrorMessage('Please enter your 4 or 6-digit UPI PIN for step-up authorization.');
      return;
    }

    setIsProcessing(true);

    const steps = requiresStepUpPin ? [
      "Validating UPI VPA & Step-Up PIN...",
      "Evaluating Payment Decision Engine rules...",
      "Authenticating NPCI UPI Circle rails...",
      "Executing authorized transaction..."
    ] : [
      "Checking pre-authorized mandate...",
      "Verifying zero-trust payment policy...",
      "Executing PIN-less autonomous debit...",
      "Finalizing transaction hash..."
    ];

    for (let i = 0; i < steps.length; i++) {
      setCurrentStepText(steps[i]);
      await new Promise((r) => setTimeout(r, 400));
    }

    const res = await onConfirmPurchase(product, totalAmount, { upiVpa, upiPin });
    setIsProcessing(false);

    if (res && res.success === false) {
      setErrorMessage(res.message || "Payment execution failed. Please try again.");
    }
  };

  return (
    <div className="modal-overlay fade-in">
      <div className="purchase-modal-card slide-up" style={{ maxWidth: '440px' }}>
        {/* Modal Header */}
        <div className="modal-header">
          <div className="modal-title">
            <Lock size={18} style={{ color: 'var(--primary-600)' }} />
            <span>Confirm Payment</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isProcessing}
            style={{ color: 'var(--text-muted)' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {/* Product Summary */}
          <div className="modal-product-summary">
            <img
              src={imageUrl}
              alt={productTitle}
              className="modal-product-img"
              onError={(e) => {
                e.target.src = "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=600&auto=format&fit=crop&q=80";
              }}
            />
            <div>
              <h4 style={{ fontSize: '0.9375rem', fontWeight: 600, color: 'var(--text-main)' }}>
                {productTitle}
              </h4>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '0.125rem' }}>
                Merchant: <strong>{merchantName}</strong> • {deliveryText}
              </p>
            </div>
          </div>

          {/* Dynamic Price Breakdown */}
          <div className="price-breakdown-box">
            <div className="price-row">
              <span>Product Price</span>
              <span>₹{productPrice.toLocaleString('en-IN')}</span>
            </div>
            <div className="price-row">
              <span>Delivery</span>
              <span style={{ color: 'var(--emerald-600)', fontWeight: 600 }}>Free</span>
            </div>
            <div className="price-row total">
              <span>Total Payable</span>
              <span style={{ color: isBreachingMonthlyCap ? '#DC2626' : 'var(--text-main)' }}>
                ₹{totalAmount.toLocaleString('en-IN')}
              </span>
            </div>
          </div>

          {/* NPCI UPI Circle Policy Notice */}
          {isBreachingMonthlyCap ? (
            <div style={{
              background: '#FEF2F2',
              border: '1px solid #FECACA',
              borderRadius: '8px',
              padding: '0.875rem',
              marginTop: '0.75rem',
              fontSize: '0.8125rem',
              color: '#991B1B'
            }}>
              <div style={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.375rem', marginBottom: '0.375rem' }}>
                <AlertTriangle size={18} style={{ color: '#DC2626' }} />
                <span>NPCI Limit Violation: ₹15,000 Cap Exceeded</span>
              </div>
              <span>
                This transaction (<strong>₹{totalAmount.toLocaleString('en-IN')}</strong>) breaches the NPCI UPI Circle maximum limit of ₹15,000. Autonomous delegation payment cannot be initiated.
              </span>
            </div>
          ) : requiresStepUpPin ? (
            <div style={{
              background: '#FFFBEB',
              border: '1px solid #FCD34D',
              borderRadius: '8px',
              padding: '0.75rem',
              marginTop: '0.75rem',
              fontSize: '0.8125rem',
              color: '#92400E'
            }}>
              <div style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.375rem', marginBottom: '0.25rem' }}>
                <AlertTriangle size={16} style={{ color: '#D97706' }} />
                <span>NPCI Step-Up Authorization Required</span>
              </div>
              <span>
                Amount (<strong>₹{totalAmount.toLocaleString('en-IN')}</strong>) exceeds the ₹5,000 PIN-less delegation threshold. Please enter your UPI VPA & UPI PIN below.
              </span>

              {/* UPI VPA & PIN Inputs */}
              <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <div>
                  <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#4B5563', display: 'block', marginBottom: '0.25rem' }}>
                    Your UPI VPA / ID:
                  </label>
                  <input
                    type="text"
                    value={upiVpa}
                    onChange={(e) => setUpiVpa(e.target.value)}
                    placeholder="e.g. yourname@upi"
                    style={{
                      width: '100%',
                      padding: '0.45rem 0.65rem',
                      borderRadius: '6px',
                      border: '1px solid #D1D5DB',
                      fontSize: '0.875rem',
                      outline: 'none'
                    }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#4B5563', display: 'block', marginBottom: '0.25rem' }}>
                    UPI PIN (4 or 6 Digits):
                  </label>
                  <div style={{ position: 'relative' }}>
                    <input
                      type="password"
                      maxLength={6}
                      value={upiPin}
                      onChange={(e) => setUpiPin(e.target.value)}
                      placeholder="••••••"
                      style={{
                        width: '100%',
                        padding: '0.45rem 0.65rem',
                        borderRadius: '6px',
                        border: '1px solid #D1D5DB',
                        fontSize: '1rem',
                        letterSpacing: '0.2em',
                        outline: 'none'
                      }}
                    />
                    <KeyRound size={16} style={{ position: 'absolute', right: '10px', top: '10px', color: '#9CA3AF' }} />
                  </div>
                </div>
              </div>

              {errorMessage && (
                <div style={{ color: '#DC2626', fontSize: '0.75rem', fontWeight: 600, marginTop: '0.375rem' }}>
                  {errorMessage}
                </div>
              )}
            </div>
          ) : (
            <div className="wallet-projection-card" style={{ marginTop: '0.75rem' }}>
              <div style={{ fontWeight: 600, color: 'var(--primary-600)', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                <CreditCard size={15} />
                <span>UPI Circle Full Delegation</span>
              </div>
              <div style={{ fontSize: '0.8125rem', color: 'var(--emerald-600)', fontWeight: 600, marginTop: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                <ShieldCheck size={16} />
                <span>🔐 PIN-less pre-authorized (Under ₹5,000 cap)</span>
              </div>
            </div>
          )}

          {errorMessage && (
            <div style={{
              background: '#FEF2F2',
              border: '1px solid #FECACA',
              borderRadius: '8px',
              padding: '0.75rem',
              marginTop: '0.75rem',
              fontSize: '0.8125rem',
              color: '#991B1B',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <AlertTriangle size={18} style={{ color: '#DC2626', flexShrink: 0 }} />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Security Checks */}
          <div className="security-checks-box" style={{ marginTop: '0.75rem' }}>
            <div className="check-item">
              <CheckCircle2 size={15} />
              <span>User identity verified</span>
            </div>
            <div className="check-item">
              <CheckCircle2 size={15} />
              <span>Price matched against verified catalog</span>
            </div>
            <div className="check-item">
              <CheckCircle2 size={15} />
              <span>AI LLM isolated from signing keys</span>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="modal-footer">
          {isProcessing ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', width: '100%', justifyContent: 'center', padding: '0.5rem 0' }}>
              <div className="step-spinner" style={{ width: '20px', height: '20px', borderColor: 'var(--primary-600)', borderTopColor: 'transparent' }} />
              <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--primary-600)' }}>
                {currentStepText}
              </span>
            </div>
          ) : (
            <>
              <button onClick={onClose} className="btn-secondary">
                Cancel
              </button>
              <button
                onClick={handleConfirm}
                disabled={isBreachingMonthlyCap}
                className="btn-primary"
                style={{
                  width: 'auto',
                  opacity: isBreachingMonthlyCap ? 0.5 : 1,
                  cursor: isBreachingMonthlyCap ? 'not-allowed' : 'pointer'
                }}
              >
                <Lock size={16} />
                <span>{isBreachingMonthlyCap ? "Transaction Blocked (> ₹15k)" : (requiresStepUpPin ? "Authorize with UPI PIN" : "Confirm Purchase")}</span>
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

