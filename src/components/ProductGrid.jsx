import React from 'react';
import ProductCard from './ProductCard';

/**
 * ProductGrid Component
 * Layout container holding top-ranked semantic recommendations.
 */
export default function ProductGrid({ products, onSelectProduct, totalAnalyzed = 47 }) {
  if (!products || products.length === 0) return null;

  return (
    <div className="product-grid-container fade-in">
      <div className="product-grid-header">
        <h2 className="product-grid-title">Best matches</h2>
        <div className="product-analysis-meta">
          {totalAnalyzed} products analyzed • Top {products.length} selected
        </div>
      </div>

      <div className="products-cards-layout">
        {products.map((product) => (
          <ProductCard
            key={product.id}
            product={product}
            onSelectProduct={onSelectProduct}
          />
        ))}
      </div>
    </div>
  );
}
