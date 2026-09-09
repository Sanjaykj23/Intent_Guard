import React from 'react';
import { Sparkles, Plus, MessageSquare, ShieldCheck, X } from 'lucide-react';

/**
 * Sidebar Component
 * Manages navigation, clean conversation sessions, and payment protection status.
 * Contains NO dummy fake chats, NO wallet balances, and NO Agent Controls.
 */
export default function Sidebar({
  isOpen,
  onClose,
  onNewChat,
  sessionChats = [],
  activeChatId,
  onSelectChat
}) {
  return (
    <aside className={`app-sidebar ${isOpen ? 'open' : ''}`}>
      <div>
        {/* Brand Header */}
        <div className="sidebar-brand">
          <Sparkles className="sparkle-icon" size={22} />
          <div>
            <span>Intent Guard</span>
            <span className="sidebar-subtext">AI Transaction Agent</span>
          </div>
          {onClose && (
            <button className="mobile-menu-btn" onClick={onClose} style={{ marginLeft: 'auto' }}>
              <X size={20} />
            </button>
          )}
        </div>

        {/* New Chat Action */}
        <button onClick={onNewChat} className="btn-new-chat">
          <Plus size={18} />
          <span>New Chat</span>
        </button>

        {/* Dynamic Session History (Empty Initially) */}
        {sessionChats.length > 0 && (
          <>
            <div className="recent-chats-label">Recent Conversations</div>
            <div className="recent-chats-list">
              {sessionChats.map((chat) => (
                <button
                  key={chat.id}
                  onClick={() => onSelectChat(chat)}
                  className={`recent-chat-item ${activeChatId === chat.id ? 'active' : ''}`}
                >
                  <MessageSquare size={15} />
                  <span>{chat.title}</span>
                </button>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Sidebar Footer Security Status */}
      <div className="sidebar-bottom">
        <div className="security-note-box">
          <div className="security-note-title">
            <ShieldCheck size={16} />
            <span>Payment Protected</span>
          </div>
          <div>AI never sees payment credentials</div>
        </div>
      </div>
    </aside>
  );
}
