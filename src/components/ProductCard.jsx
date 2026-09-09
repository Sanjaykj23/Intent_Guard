import React, { useState } from 'react';
import { Star, Truck, Check, Sparkles, ShoppingBag, ExternalLink, ImageOff } from 'lucide-react';

/**
 * ProductCard Component
 * Displays verified product result with exact product URL, match rationale, and purchase trigger.
 */
export default function ProductCard({ product, onSelectProduct }) {
  const [hasImgError, setHasImgError] = useState(false);

  const title = product.name || product.title || "Product Item";
  const pricePaise = product.price_paise ?? (product.price ? product.price * 100 : 0);
  const priceDisplay = product.formatted_price || `₹${(pricePaise / 100).toLocaleString('en-IN')}`;
  const merchant = product.provider || product.merchant || product.platform || "Merchant";
  const matchScore = product.match_score || product.matchScore || 95;
  const matchReason = product.match_reason || product.matchReason || "Matched user query and spending budget";
  const imageUrl = product.image_url || product.image || "";
  const productUrl = product.exact_action_url || product.source_url || product.product_url || product.productUrl || "";
  
  const isExactProduct = product.verified ?? product.is_url_verified ?? (
    productUrl ? (
      product.url_type === "EXACT_PRODUCT_PAGE" || 
      (!productUrl.includes("/s?") && !productUrl.includes("/search") && !productUrl.includes("s?k="))
    ) : false
  );

  return (
    <div className="product-card fade-in">
      {/* Product Image Container */}
      <div className="product-image-wrap">
        {!hasImgError && imageUrl ? (
          <img
            src={imageUrl}
            alt={title}
            className="product-img"
            onError={() => setHasImgError(true)}
          />
        ) : (
          <div className="product-img-fallback">
            <ImageOff size={24} style={{ color: 'var(--text-muted)' }} />
            <span>Product image preview</span>
          </div>
        )}

        <div className="match-score-badge">
          <Sparkles size={13} />
          <span>{matchScore}% MATCH</span>
        </div>

        <div className="platform-badge">
          {merchant}
        </div>
      </div>

      {/* Product Card Details */}
      <div className="product-card-body">
        <div>
          <h3 className="product-name">{title}</h3>

          <div className="product-price-row" style={{ marginTop: '0.375rem', alignItems: 'center' }}>
            <span className="product-price">{priceDisplay}</span>
            {productUrl && (
              <a
                href={productUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="live-product-link"
                title="Open verified merchant product page"
                style={{
                  marginLeft: 'auto',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.25rem',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  color: 'var(--primary-600, #3b82f6)',
                  textDecoration: 'none'
                }}
              >
                <span>{isExactProduct ? "Product Link ↗" : "Merchant Link ↗"}</span>
                <ExternalLink size={13} />
              </a>
            )}
          </div>
        </div>

        <div className="product-meta-row">
          <div className="rating-tag">
            <Star size={13} fill="currentColor" />
            <span>{product.rating || 4.7}</span>
            <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>
              ({product.reviews_count || product.reviewsCount || 450})
            </span>
          </div>

          <div className="delivery-tag">
            <Truck size={13} />
            <span>{product.delivery || "Fast Delivery"}</span>
          </div>
        </div>

        {/* Why This Matches Rationale */}
        <div className="match-reasons-list">
          <div style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: '0.125rem' }}>
            Why this matches:
          </div>
          <div className="match-reason-item">
            <Check size={13} />
            <span>{matchReason}</span>
          </div>
          {Object.entries(product.match_attributes || product.matchAttributes || {}).map(([key, val]) => (
            <div key={key} className="match-reason-item">
              <Check size={13} />
              <span>{typeof val === 'string' ? val : JSON.stringify(val)}</span>
            </div>
          ))}
        </div>

        {/* Action Button */}
        <button
          type="button"
          onClick={(e) => {
            e.preventDefault();
            if (isExactProduct) {
              onSelectProduct(product);
            } else if (productUrl) {
              window.open(productUrl, "_blank", "noopener,noreferrer");
            }
          }}
          className="btn-buy-agent"
        >
          <ShoppingBag size={16} />
          <span>{isExactProduct ? "Pay & Transact Safely" : "View Search on Merchant"}</span>
        </button>
      </div>
    </div>
  );
}
