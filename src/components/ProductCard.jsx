import React, { useState } from 'react';
import { Star, Truck, Check, Sparkles, ShoppingBag, ImageOff } from 'lucide-react';

/**
 * ProductCard Component
 * Displays product result with verified image relevance, match rationale, and purchase trigger.
 */
export default function ProductCard({ product, onSelectProduct }) {
  const [hasImgError, setHasImgError] = useState(false);

  return (
    <div className="product-card fade-in">
      {/* Product Image Container */}
      <div className="product-image-wrap">
        {!hasImgError && product.image ? (
          <img
            src={product.image}
            alt={product.name}
            className="product-img"
            onError={() => setHasImgError(true)}
          />
        ) : (
          /* Neutral Fallback Placeholder (Never show unrelated image) */
          <div className="product-img-fallback">
            <ImageOff size={24} style={{ color: 'var(--text-muted)' }} />
            <span>Product image unavailable</span>
          </div>
        )}

        <div className="match-score-badge">
          <Sparkles size={13} />
          <span>{product.matchScore}% MATCH</span>
        </div>

        <div className="platform-badge">
          {product.platform}
        </div>
      </div>

      {/* Product Card Details */}
      <div className="product-card-body">
        <div>
          <h3 className="product-name">{product.name}</h3>

          <div className="product-price-row" style={{ marginTop: '0.375rem' }}>
            <span className="product-price">₹{product.price.toLocaleString('en-IN')}</span>
            {product.originalPrice && product.originalPrice > product.price && (
              <span className="product-original-price">
                ₹{product.originalPrice.toLocaleString('en-IN')}
              </span>
            )}
          </div>
        </div>

        <div className="product-meta-row">
          <div className="rating-tag">
            <Star size={13} fill="currentColor" />
            <span>{product.rating}</span>
            <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>
              ({product.reviewsCount})
            </span>
          </div>

          <div className="delivery-tag">
            <Truck size={13} />
            <span>{product.delivery}</span>
          </div>
        </div>

        {/* Why This Matches Rationale */}
        <div className="match-reasons-list">
          <div style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: '0.125rem' }}>
            Why this matches:
          </div>
          {Object.entries(product.matchAttributes || {}).map(([key, val]) => (
            <div key={key} className="match-reason-item">
              <Check size={13} />
              <span>{val}</span>
            </div>
          ))}
        </div>

        {/* Buy Action Button */}
        <button
          onClick={() => onSelectProduct(product)}
          className="btn-buy-agent"
        >
          <ShoppingBag size={16} />
          <span>Buy with Agent</span>
        </button>
      </div>
    </div>
  );
}
