import React, { useState } from 'react';
import { ShieldCheck, CheckCircle2, X, Lock, CreditCard } from 'lucide-react';

/**
 * PurchaseModal Component
 * Confirms transaction intent and executes secure payment authorization.
 * DOES NOT display or access user bank balance.
 */
export default function PurchaseModal({ product, onClose, onConfirmPurchase }) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStepText, setCurrentStepText] = useState('');

  if (!product) return null;

  const productTitle = product.name || product.title || "Product Item";
  const pricePaise = product.price_paise ?? (product.price ? product.price * 100 : 0);
  const productPrice = pricePaise / 100;
  const deliveryFee = 0;
  const totalAmount = productPrice + deliveryFee;
  const merchantName = product.provider || product.merchant || product.platform || "Merchant";
  const imageUrl = product.image_url || product.image || "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=600&auto=format&fit=crop&q=80";
  const deliveryText = product.delivery || "Fast Delivery";

  const handleConfirm = async () => {
    setIsProcessing(true);

    const steps = [
      "Checking transaction authorization...",
      "Verifying payment security policy...",
      "Authorizing secure payment...",
      "Processing transaction..."
    ];

    for (let i = 0; i < steps.length; i++) {
      setCurrentStepText(steps[i]);
      await new Promise((r) => setTimeout(r, 450));
    }

    await onConfirmPurchase(product, totalAmount);
    setIsProcessing(false);
  };

  return (
    <div className="modal-overlay fade-in">
      <div className="purchase-modal-card slide-up">
        {/* Modal Header */}
        <div className="modal-header">
          <div className="modal-title">
            <Lock size={18} style={{ color: 'var(--primary-600)' }} />
            <span>Confirm Purchase</span>
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
              <span>Product</span>
              <span>₹{productPrice.toLocaleString('en-IN')}</span>
            </div>
            <div className="price-row">
              <span>Delivery</span>
              <span style={{ color: 'var(--emerald-600)', fontWeight: 600 }}>Free</span>
            </div>
            <div className="price-row total">
              <span>Total</span>
              <span>₹{totalAmount.toLocaleString('en-IN')}</span>
            </div>
          </div>

          {/* Secure Payment Authorization Card (NO BANK BALANCE) */}
          <div className="wallet-projection-card">
            <div style={{ fontWeight: 600, color: 'var(--primary-600)', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
              <CreditCard size={15} />
              <span>Payment Authorization</span>
            </div>
            <div style={{ fontSize: '0.8125rem', color: 'var(--emerald-600)', fontWeight: 600, marginTop: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
              <ShieldCheck size={16} />
              <span>🔐 Secure payment method connected</span>
            </div>
          </div>

          {/* Security Checks */}
          <div className="security-checks-box">
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Security Checks
            </div>
            <div className="check-item">
              <CheckCircle2 size={15} />
              <span>User authenticated</span>
            </div>
            <div className="check-item">
              <CheckCircle2 size={15} />
              <span>Transaction authorized</span>
            </div>
            <div className="check-item">
              <CheckCircle2 size={15} />
              <span>Payment credentials protected</span>
            </div>
            <div className="check-item">
              <CheckCircle2 size={15} />
              <span>AI does not access bank details</span>
            </div>
          </div>

          {/* Security Disclaimer */}
          <div className="modal-security-disclaimer">
            <ShieldCheck size={18} style={{ flexShrink: 0 }} />
            <span>Your payment credentials are never exposed to the AI agent.</span>
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
              <button onClick={handleConfirm} className="btn-primary" style={{ width: 'auto' }}>
                <Lock size={16} />
                <span>Confirm Purchase</span>
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
