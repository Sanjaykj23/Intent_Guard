import React from 'react';
import { TrendingUp, PackagePlus, Sparkles, Tag, ArrowRight } from 'lucide-react';

/**
 * RevenueBanner Component
 * Displays Merchant Growth & Monetization Suggestions (Upsell, Cross-Sell, Smart Bundle)
 */
export default function RevenueBanner({ recommendations, onSelectProduct }) {
  if (!recommendations) return null;

  const { upsell, cross_sell, bundle } = recommendations;
  if (!upsell && (!cross_sell || cross_sell.length === 0) && !bundle) return null;

  return (
    <div className="revenue-banner-container fade-in" style={{
      margin: '1rem 0',
      padding: '1rem',
      background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.06), rgba(59, 130, 246, 0.06))',
      border: '1px solid rgba(16, 185, 129, 0.2)',
      borderRadius: '0.75rem'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', color: 'var(--emerald-600, #059669)', fontWeight: 600, fontSize: '0.875rem' }}>
        <TrendingUp size={18} />
        <span>Merchant Partner Growth & Smart Offers</span>
      </div>

      {/* Smart Bundle Card */}
      {bundle && (
        <div style={{
          padding: '0.875rem',
          background: 'rgba(255, 255, 255, 0.8)',
          border: '1px dashed var(--emerald-500, #10b981)',
          borderRadius: '0.5rem',
          marginBottom: '0.75rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', color: 'var(--emerald-700, #047857)', fontWeight: 700, fontSize: '0.875rem' }}>
              <Tag size={16} />
              <span>{bundle.title}</span>
            </div>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, background: 'rgba(16, 185, 129, 0.15)', color: 'var(--emerald-700)', padding: '0.125rem 0.5rem', borderRadius: '1rem' }}>
              {bundle.savings_formatted}
            </span>
          </div>

          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: '0.375rem 0' }}>
            Includes: {bundle.items.join(' + ')}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '0.5rem' }}>
            <span style={{ fontWeight: 700, color: 'var(--text-main)', fontSize: '0.9375rem' }}>
              Bundle Price: {bundle.formatted_bundle_price}
            </span>
            <button
              onClick={() => onSelectProduct && onSelectProduct({ title: bundle.title, price: bundle.bundle_price_paise / 100, merchant: bundle.merchant })}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.25rem',
                fontSize: '0.75rem',
                fontWeight: 600,
                color: '#fff',
                background: 'var(--emerald-600, #059669)',
                border: 'none',
                padding: '0.375rem 0.75rem',
                borderRadius: '0.375rem',
                cursor: 'pointer'
              }}
            >
              <span>Add Bundle Offer</span>
              <ArrowRight size={13} />
            </button>
          </div>
        </div>
      )}

      {/* Upsell Card */}
      {upsell && (
        <div style={{
          padding: '0.75rem',
          background: 'rgba(59, 130, 246, 0.06)',
          border: '1px solid rgba(59, 130, 246, 0.15)',
          borderRadius: '0.5rem',
          marginBottom: '0.5rem',
          fontSize: '0.8125rem'
        }}>
          <div style={{ fontWeight: 600, color: 'var(--primary-700, #1d4ed8)', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
            <Sparkles size={14} />
            <span>Recommended Variant Upgrade: {upsell.title} ({upsell.formatted_price})</span>
          </div>
          <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-muted)', fontSize: '0.75rem' }}>{upsell.description}</p>
        </div>
      )}

      {/* Cross Sell Items */}
      {cross_sell && cross_sell.length > 0 && (
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>Frequently Bought Together: </span>
          {cross_sell.map((cs) => cs.title).join(', ')}
        </div>
      )}
    </div>
  );
}
