import React, { useRef, useEffect } from 'react';
import { ArrowRight } from 'lucide-react';
import Message from './Message';
import AgentActivity from './AgentActivity';
import ProductGrid from './ProductGrid';
import SuccessMessage from './SuccessMessage';

/**
 * ChatWindow Component
 * Manages the continuous message stream, auto-scrolling, universal welcome screen,
 * and orchestrates independent components (AgentActivity, ProductGrid, SuccessMessage).
 */
export default function ChatWindow({
  messages,
  onSendSuggestion,
  isProcessingActivity,
  activityStepIndex,
  isActivityComplete,
  products,
  onSelectProduct,
  completedTransaction,
  onContinueShopping
}) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activityStepIndex, products, completedTransaction]);

  const suggestions = [
    { id: 1, text: "Find me a black oversized shirt under ₹1500" },
    { id: 2, text: "Find wireless earbuds under ₹2000" },
    { id: 3, text: "Order dinner for two under ₹800" },
    { id: 4, text: "Recharge my phone with the best ₹299 plan" }
  ];

  return (
    <div className="chat-area">
      <div className="messages-scroll-container">
        {messages.length === 0 ? (
          /* Universal Welcome Screen */
          <div className="welcome-container fade-in">
            <div className="welcome-logo-sparkle">✦</div>
            <h1 className="welcome-title">What do you want me to take care of?</h1>
            <p className="welcome-subtitle">
              Tell me your intent. I'll find, compare and help execute it securely.
            </p>

            <div className="suggestions-grid">
              {suggestions.map((item) => (
                <div
                  key={item.id}
                  onClick={() => onSendSuggestion(item.text)}
                  className="suggestion-card"
                  role="button"
                  tabIndex={0}
                >
                  <p className="suggestion-text">{item.text}</p>
                  <div className="suggestion-arrow">
                    <span>Try intent</span>
                    <ArrowRight size={13} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          /* Continuous Conversation Stream */
          <div className="messages-inner">
            {messages.map((msg) => (
              <Message key={msg.id} message={msg} />
            ))}

            {/* Agent Activity Visualization */}
            {isProcessingActivity && (
              <AgentActivity
                currentStepIndex={activityStepIndex}
                isComplete={isActivityComplete}
              />
            )}

            {/* Product Recommendations Grid */}
            {isActivityComplete && products && products.length > 0 && !completedTransaction && (
              <ProductGrid
                products={products}
                onSelectProduct={onSelectProduct}
              />
            )}

            {/* Success Message Receipt */}
            {completedTransaction && (
              <SuccessMessage
                transaction={completedTransaction}
                onContinueShopping={onContinueShopping}
              />
            )}

            <div ref={bottomRef} />
          </div>
        )}
      </div>
    </div>
  );
}
