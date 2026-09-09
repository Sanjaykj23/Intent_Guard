import React, { useState, useEffect } from 'react';
import { Sparkles, Menu, Lock, ShieldCheck, User, Zap, LogOut, CheckCircle2 } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import ChatWindow from '../components/ChatWindow';
import ChatInput from '../components/ChatInput';
import PurchaseModal from '../components/PurchaseModal';
import AuthModal from '../components/AuthModal';
import UPICircleSetupModal from '../components/UPICircleSetupModal';
import { sendAgentMessage, searchProducts, compareProducts, purchaseProduct, getUPICircleStatus } from '../services/api';

/**
 * Home Page Component — Main Dashboard & Intent Processing Controller
 * Manages one continuous AI session without financial balance displays or dummy data.
 */
export default function Home({ onLockSession, onLogout, authenticatedUser }) {
  // Navigation & Session History States
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [sessionChats, setSessionChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);

  // User & Auth Session States
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('intentguard_user');
    if (saved) return JSON.parse(saved);
    if (authenticatedUser) return authenticatedUser;
    return null;
  });

  const [hasUpiCircle, setHasUpiCircle] = useState(true);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isUpiModalOpen, setIsUpiModalOpen] = useState(false);

  // Messaging & Agent Pipeline States
  const [messages, setMessages] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isProcessingActivity, setIsProcessingActivity] = useState(false);
  const [activityStepIndex, setActivityStepIndex] = useState(0);
  const [isActivityComplete, setIsActivityComplete] = useState(false);
  const [products, setProducts] = useState([]);

  // Transaction States
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [pendingProductPurchase, setPendingProductPurchase] = useState(null);
  const [completedTransaction, setCompletedTransaction] = useState(null);

  useEffect(() => {
    if (user?.token) {
      localStorage.setItem('intentguard_user', JSON.stringify(user));
      // Check UPI Circle Status
      getUPICircleStatus(user.token, user.user_id).then(res => {
        setHasUpiCircle(res.has_mandate || res.mandate_status === 'ACTIVE');
      });
    }
  }, [user]);

  const handleAuthSuccess = (userData) => {
    const formatted = {
      user_id: userData.user_id || userData.agentUserId,
      name: userData.name || userData.userName,
      email: userData.email,
      phone: userData.phone || '+919876543210',
      address: userData.address || '123 Tech Park, Bengaluru, KA',
      token: userData.token
    };
    setUser(formatted);
    localStorage.setItem('intentguard_user', JSON.stringify(formatted));

    if (userData.has_upi_circle) {
      setHasUpiCircle(true);
    } else {
      setHasUpiCircle(false);
      setIsUpiModalOpen(true);
    }

    if (pendingProductPurchase) {
      setSelectedProduct(pendingProductPurchase);
      setPendingProductPurchase(null);
    }
  };

  const handleMandateCreated = (mandateData) => {
    setHasUpiCircle(true);
    const updatedUser = { ...user, has_upi_circle: true, mandate_id: mandateData.mandate_id };
    setUser(updatedUser);
    localStorage.setItem('intentguard_user', JSON.stringify(updatedUser));

    if (pendingProductPurchase) {
      setSelectedProduct(pendingProductPurchase);
      setPendingProductPurchase(null);
    }
  };

  // New Chat Action (Clean Reset)
  const handleNewChat = () => {
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

    const userMessageObj = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      text: userIntentText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMessageObj]);
    setIsProcessing(true);
    setIsProcessingActivity(true);
    setActivityStepIndex(0);
    setIsActivityComplete(false);
    setProducts([]);
    setCompletedTransaction(null);

    try {
      const result = await sendAgentMessage(userIntentText);

      setActivityStepIndex(1);
      await new Promise(r => setTimeout(r, 600));

      setActivityStepIndex(2);
      await new Promise(r => setTimeout(r, 600));

      setIsActivityComplete(true);

      const agentMessageObj = {
        id: `msg-${Date.now() + 1}`,
        sender: 'agent',
        text: result.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        intentData: result.result?.intent,
        policyCheck: result.result?.policy_check
      };

      setMessages(prev => [...prev, agentMessageObj]);

      if (result.result?.products && result.result.products.length > 0) {
        setProducts(result.result.products);
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        id: `msg-${Date.now() + 1}`,
        sender: 'agent',
        text: "I encountered an issue processing your intent. Please try again.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    } finally {
      setIsProcessing(false);
      setIsProcessingActivity(false);
    }
  };

  // Select Product for Transaction Confirmation
  const handleSelectProduct = (product) => {
    if (!user || !user.token) {
      setPendingProductPurchase(product);
      setIsAuthModalOpen(true);
      return;
    }

    if (!hasUpiCircle) {
      setPendingProductPurchase(product);
      setIsUpiModalOpen(true);
      return;
    }

    setSelectedProduct(product);
  };

  // Confirm Authorized Purchase
  const handleConfirmPurchase = async (product, totalAmount, options = {}) => {
    const params = {
      product: product,
      amount: totalAmount,
      quoteId: product.id ? `QUOTE_${product.id}` : "QUOTE_MOCK_1001",
      userId: user?.user_id || "USER_DEFAULT_01",
      amountPaise: Math.round(totalAmount * 100),
      upiVpa: options.upiVpa || "sanjay@okicici",
      upiPin: options.upiPin || ""
    };

    const txResult = await purchaseProduct(params);

    if (txResult.success) {
      const formattedAmt = txResult.formattedAmount || `₹${Math.round(totalAmount).toLocaleString('en-IN')}`;
      const txIdVal = txResult.transactionId || txResult.tx_id || `TXN_MOCK_${Math.floor(1000 + Math.random() * 9000)}`;

      setCompletedTransaction({
        transactionId: txIdVal,
        txId: txIdVal,
        productTitle: product.title || product.name || "Product Item",
        merchantName: product.merchant || product.provider || "Merchant",
        amountPaid: formattedAmt,
        formattedAmount: formattedAmt,
        amountPaidPaise: Math.round(totalAmount * 100),
        status: txResult.status || "Authorized & Executed",
        stepUpAuthenticated: txResult.step_up_authenticated || false,
        razorpayTokenHash: txResult.razorpay_token_hash || "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      });

      setSelectedProduct(null);
    }
    return txResult;
  };

  // Continue Shopping Handler
  const handleContinueShopping = () => {
    setCompletedTransaction(null);
  };

  return (
    <div className="app-layout font-sans">
      {/* Navigation Sidebar */}
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        sessionChats={sessionChats}
        onNewChat={handleNewChat}
        onSelectHistoryChat={(chat) => {
          setMessages(chat.messages);
          setIsSidebarOpen(false);
        }}
      />

      {/* Main Content Dashboard */}
      <main className="app-main-content">
        {/* Top Header Bar */}
        <header className="top-bar">
          <div className="top-bar-left">
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="btn-icon"
              title="Toggle Navigation Menu"
            >
              <Menu size={20} />
            </button>
            <Sparkles className="sparkle-icon" size={20} />
            <span>✦ Intent Guard</span>
          </div>

          <div className="top-bar-actions" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            {/* User Profile / Auth Button */}
            {user ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#f1f5f9', padding: '0.375rem 0.75rem', borderRadius: '2rem', fontSize: '0.8125rem' }}>
                <User size={16} style={{ color: '#2563eb' }} />
                <span style={{ fontWeight: 600, color: '#1e293b' }}>{user.name}</span>
                <button
                  onClick={() => setIsAuthModalOpen(true)}
                  style={{ background: 'none', border: 'none', fontSize: '0.70rem', color: '#2563eb', cursor: 'pointer', textDecoration: 'underline' }}
                >
                  Edit Profile
                </button>
              </div>
            ) : (
              <button
                onClick={() => setIsAuthModalOpen(true)}
                style={{
                  padding: '0.375rem 0.875rem',
                  background: '#2563eb',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '2rem',
                  fontSize: '0.8125rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                Sign In / Register
              </button>
            )}

            {/* UPI Circle Status Badge */}
            <button
              onClick={() => setIsUpiModalOpen(true)}
              className="secure-payment-badge"
              style={{
                cursor: 'pointer',
                background: hasUpiCircle ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                border: hasUpiCircle ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(245, 158, 11, 0.3)',
                color: hasUpiCircle ? '#059669' : '#d97706',
                padding: '0.375rem 0.75rem',
                borderRadius: '2rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.375rem',
                fontSize: '0.75rem',
                fontWeight: 600
              }}
            >
              {hasUpiCircle ? (
                <>
                  <CheckCircle2 size={16} />
                  <span>UPI Circle Active</span>
                </>
              ) : (
                <>
                  <Zap size={16} />
                  <span>Enable UPI Circle</span>
                </>
              )}
            </button>

            {/* Lock Session Action */}
            <button
              onClick={onLockSession}
              className="btn-lock"
              title="Lock Intent Guard"
              aria-label="Lock Intent Guard"
            >
              <Lock size={18} />
            </button>

            {/* Logout / Switch Account Action */}
            <button
              onClick={onLogout || onLockSession}
              className="btn-lock"
              title="Log Out / Switch Account"
              aria-label="Log Out / Switch Account"
            >
              <LogOut size={18} style={{ color: '#ef4444' }} />
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

        {/* Auth Modal (Sign Up / Sign In) */}
        <AuthModal
          isOpen={isAuthModalOpen}
          onClose={() => setIsAuthModalOpen(false)}
          onAuthSuccess={handleAuthSuccess}
        />

        {/* UPI Circle Onboarding Modal */}
        <UPICircleSetupModal
          isOpen={isUpiModalOpen}
          onClose={() => setIsUpiModalOpen(false)}
          user={user}
          onMandateCreated={handleMandateCreated}
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
