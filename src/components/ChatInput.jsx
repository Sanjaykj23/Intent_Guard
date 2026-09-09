import React, { useState } from 'react';
import { Send, ShieldCheck } from 'lucide-react';

/**
 * ChatInput Component
 * Fixed bottom prompt bar supporting universal intent queries.
 */
export default function ChatInput({ onSendMessage, disabled }) {
  const [text, setText] = useState('');

  const handleSend = (e) => {
    if (e) e.preventDefault();
    if (!text.trim() || disabled) return;
    onSendMessage(text.trim());
    setText('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-input-sticky-container">
      <form onSubmit={handleSend} className="chat-input-box">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Tell me what you want me to take care of..."
          rows={2}
          className="chat-textarea"
          disabled={disabled}
        />

        <div className="chat-input-actions">
          <div className="input-security-tag">
            <ShieldCheck size={14} style={{ color: 'var(--emerald-600)' }} />
            <span>Intent Guard can search, compare and execute authorized transactions.</span>
          </div>

          <button
            type="submit"
            disabled={disabled || !text.trim()}
            className="btn-send"
            title="Send Intent"
            aria-label="Send Intent"
          >
            <Send size={16} />
          </button>
        </div>
      </form>
    </div>
  );
}
