import React, { useState } from 'react';
import { Sparkles, Menu, Lock, ShieldCheck } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import ChatWindow from '../components/ChatWindow';
import ChatInput from '../components/ChatInput';
import PurchaseModal from '../components/PurchaseModal';
import { sendAgentMessage, searchProducts, compareProducts, purchaseProduct } from '../services/api';

/**
 * Home Page Component — Main Dashboard & Intent Processing Controller
 * Manages one continuous AI session without financial balance displays or dummy data.
 */
export default function Home({ onLockSession, authenticatedUser }) {
  // Navigation & Session History States
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [sessionChats, setSessionChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);

  // Messaging & Agent Pipeline States
  const [messages, setMessages] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isProcessingActivity, setIsProcessingActivity] = useState(false);
  const [activityStepIndex, setActivityStepIndex] = useState(0);
  const [isActivityComplete, setIsActivityComplete] = useState(false);
  const [products, setProducts] = useState([]);

  // Transaction States
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [completedTransaction, setCompletedTransaction] = useState(null);

  // New Chat Action (Clean Reset)
  const handleNewChat = () => {
    // If current conversation has user messages, store title in session history
    if (messages.length > 0) {
      const firstUserMsg = messages.find(m => m.sender === 'user');
      if (firstUserMsg) {
        const newHistoryItem = {
          id: `chat-${Date.now()}`,
          title: firstUserMsg.text.length > 24 ? `${firstUserMsg.text.substring(0, 24)}...` : firstUserMsg.text,
          messages: [...messages]
        };
        setSessionChats(prev => [newHistoryItem, ...prev]);
      }
    }

    setMessages([]);
    setIsProcessingActivity(false);
    setActivityStepIndex(0);
    setIsActivityComplete(false);
    setProducts([]);
    setSelectedProduct(null);
    setCompletedTransaction(null);
    setActiveChatId(null);
    setIsSidebarOpen(false);
  };

  // Submit Intent Query
  const handleSendIntent = async (userIntentText) => {
    if (isProcessing) return;

    setCompletedTransaction(null);

    // Add User Message
    const userMsg = {
      id: `msg-user-${Date.now()}`,
      sender: 'user',
      text: userIntentText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsProcessing(true);

    try {
      // 1. Process Intent via API Service
      const agentRes = await sendAgentMessage(userIntentText);
      const agentMsg = {
        id: `msg-agent-${Date.now()}`,
        sender: 'agent',
        text: agentRes.reply || "I analyzed your intent and retrieved verified candidates.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages((prev) => [...prev, agentMsg]);

      // 2. Progressive Agent Activity Visualization Ticks
      setIsProcessingActivity(true);
      setIsActivityComplete(false);

      const totalSteps = 8;
      for (let i = 0; i < totalSteps; i++) {
        setActivityStepIndex(i);
        await new Promise((r) => setTimeout(r, 180));
      }

      // 3. Extract products for display & user decision
      let fetchedProducts = agentRes.result?.products || agentRes.products || [];
      if (!fetchedProducts || fetchedProducts.length === 0) {
        const searchRes = await searchProducts(userIntentText);
        fetchedProducts = searchRes.products || [];
      }

      setProducts(fetchedProducts);
      setIsActivityComplete(true);
    } catch (err) {
      console.error("Error processing intent:", err);
      setMessages((prev) => [
        ...prev,
        {
          id: `msg-error-${Date.now()}`,
          sender: 'agent',
          text: "Something went wrong while processing your intent. Please try again."
        }
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  // Select Product for Transaction Confirmation
  const handleSelectProduct = (product) => {
    setSelectedProduct(product);
  };

  // Confirm Authorized Purchase
  const handleConfirmPurchase = async (product, totalAmount) => {
    try {
      const txRes = await purchaseProduct({
        agentUserId: authenticatedUser?.agentUserId || "USER_4821",
        productId: product.id,
        amount: totalAmount
      });

      if (txRes.success) {
        setCompletedTransaction(txRes);
        setSelectedProduct(null);
      }
    } catch (err) {
      console.error("Purchase failed:", err);
    }
  };

  // Continue Shopping Handler
  const handleContinueShopping = () => {
    setCompletedTransaction(null);
    setProducts([]);
    setIsProcessingActivity(false);
    setIsActivityComplete(false);
  };

  return (
    <div className="app-layout">
      {/* Navigation Sidebar */}
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        onNewChat={handleNewChat}
        sessionChats={sessionChats}
        activeChatId={activeChatId}
        onSelectChat={(chat) => {
          setMessages(chat.messages || []);
          setActiveChatId(chat.id);
          setIsSidebarOpen(false);
        }}
      />

      {/* Main Content Dashboard */}
      <main className="app-main-content">
        {/* Top Header Bar */}
        <header className="top-bar">
          <div className="top-bar-title">
            <button
              className="mobile-menu-btn"
              onClick={() => setIsSidebarOpen(true)}
              aria-label="Open Sidebar"
            >
              <Menu size={22} />
            </button>
            <Sparkles className="sparkle-icon" size={20} />
            <span>✦ Intent Guard</span>
          </div>

          <div className="top-bar-actions">
            {/* Secure Payment Connected Status Badge (NO BANK BALANCE) */}
            <div className="secure-payment-badge">
              <ShieldCheck size={16} style={{ color: 'var(--emerald-600)' }} />
              <span>🔐 Secure Payment</span>
            </div>

            {/* Lock Session Action */}
            <button
              onClick={onLockSession}
              className="btn-lock"
              title="Lock Intent Guard"
              aria-label="Lock Intent Guard"
            >
              <Lock size={18} />
            </button>
          </div>
        </header>

        {/* Central Chat & Message Stream */}
        <ChatWindow
          messages={messages}
          onSendSuggestion={handleSendIntent}
          isProcessingActivity={isProcessingActivity}
          activityStepIndex={activityStepIndex}
          isActivityComplete={isActivityComplete}
          products={products}
          onSelectProduct={handleSelectProduct}
          completedTransaction={completedTransaction}
          onContinueShopping={handleContinueShopping}
        />

        {/* Sticky Input Bar */}
        <ChatInput
          onSendMessage={handleSendIntent}
          disabled={isProcessing}
        />

        {/* Purchase Confirmation Security Modal */}
        {selectedProduct && (
          <PurchaseModal
            product={selectedProduct}
            onClose={() => setSelectedProduct(null)}
            onConfirmPurchase={handleConfirmPurchase}
          />
        )}
      </main>
    </div>
  );
}
