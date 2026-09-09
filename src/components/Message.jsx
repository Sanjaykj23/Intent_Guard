import React from 'react';
import { Sparkles, User } from 'lucide-react';

/**
 * Message Component — Single Responsibility
 * Strictly renders individual chat messages (user & agent bubbles, text, avatars).
 * Does NOT render AgentActivity, ProductGrid, or SuccessMessage.
 */
export default function Message({ message }) {
  const isUser = message.sender === 'user';

  return (
    <div className={`message-bubble-wrapper ${isUser ? 'user' : 'agent'} fade-in`}>
      <div className={`avatar ${isUser ? 'user' : 'agent'}`}>
        {isUser ? <User size={18} /> : <Sparkles size={18} />}
      </div>

      <div className="message-content-box">
        <div className="message-sender-name">
          {isUser ? 'You' : '✦ Intent Guard'}
        </div>
        <div className="message-text-card">
          {message.text}
        </div>
      </div>
    </div>
  );
}
