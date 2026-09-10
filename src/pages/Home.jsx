import React, { useState, useEffect } from 'react';
import { Sparkles, Menu, Lock, ShieldCheck, User, Zap, LogOut, CheckCircle2, RefreshCw } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import ChatWindow from '../components/ChatWindow';
import ChatInput from '../components/ChatInput';
import PurchaseModal from '../components/PurchaseModal';
import AuthModal from '../components/AuthModal';
import UPICircleSetupModal from '../components/UPICircleSetupModal';
import UPICircleDashboard from '../components/UPICircleDashboard';
import PaymentApprovalCard from '../components/PaymentApprovalCard';
import { sendAgentMessage, purchaseProduct, getUPICircleStatus, evaluatePaymentDecision, initiatePaymentDecision, resetDemoData } from '../services/api';

/**
 * Home Page Component — Main Dashboard & Intent Processing Controller
 * Full Hackathon Prototype for AI Chatbot + Payment Decision Engine + Simulated UPI Circle + Mock Bank
 */
export default function Home({ onLockSession, onLogout, authenticatedUser }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [sessionChats, setSessionChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);

  const [user, setUser] = useState(() => {
    if (authenticatedUser) return authenticatedUser;
    const saved = localStorage.getItem('intentguard_user');
    if (saved) return JSON.parse(saved);
    return { user_id: 'USER_DEFAULT_001', name: 'Sanjay Demo User', email: 'sanjay@demo.ai' };
  });

  const [hasUpiCircle, setHasUpiCircle] = useState(true);
  const [showDashboard, setShowDashboard] = useState(true);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isUpiModalOpen, setIsUpiModalOpen] = useState(false);

  const [messages, setMessages] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isProcessingActivity, setIsProcessingActivity] = useState(false);
  const [activityStepIndex, setActivityStepIndex] = useState(0);
  const [isActivityComplete, setIsActivityComplete] = useState(false);
  const [products, setProducts] = useState([]);

  const [selectedProduct, setSelectedProduct] = useState(null);
  const [pendingProductPurchase, setPendingProductPurchase] = useState(null);
  const [completedTransaction, setCompletedTransaction] = useState(null);
  const [pendingApproval, setPendingApproval] = useState(null);
  const [dashboardKey, setDashboardKey] = useState(0);

  useEffect(() => {
    if (authenticatedUser) {
      setUser(authenticatedUser);
    }
  }, [authenticatedUser]);

  useEffect(() => {
    if (user?.user_id) {
      getUPICircleStatus(user.token, user.user_id).then(res => {
        setHasUpiCircle(res.has_mandate);
      });
      refreshDashboard();
    }
  }, [user]);

  const refreshDashboard = () => {
    setDashboardKey(prev => prev + 1);
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new Event('upi_circle_updated'));
    }
  };

  const handleAuthSuccess = (userData) => {
    const formatted = {
      user_id: userData.user_id || 'USER_DEFAULT_001',
      name: userData.name || 'Sanjay Demo User',
      email: userData.email,
      phone: userData.phone || '+919876543210',
      address: userData.address || '123 Tech Park, Bengaluru, KA',
      token: userData.token
    };
    setUser(formatted);
    localStorage.setItem('intentguard_user', JSON.stringify(formatted));
    setHasUpiCircle(true);
    refreshDashboard();
  };

  const handleMandateCreated = () => {
    setHasUpiCircle(true);
    refreshDashboard();
  };

  const handleNewChat = () => {
    setMessages([]);
    setIsProcessingActivity(false);
    setActivityStepIndex(0);
    setIsActivityComplete(false);
    setProducts([]);
    setSelectedProduct(null);
    setCompletedTransaction(null);
    setPendingApproval(null);
    setActiveChatId(null);
    setIsSidebarOpen(false);
  };

  // Process natural language payment intent
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
    setPendingApproval(null);

    // Detect payment amounts & categories from natural language
    const textLower = userIntentText.toLowerCase();
    const priceMatch = userIntentText.match(/(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?)/i);
    const amountVal = priceMatch ? parseFloat(priceMatch[1].replace(/,/g, '')) : null;

    let category = "SHOPPING";
    let merchant = "Demo Store";

    if (textLower.includes("grocery") || textLower.includes("groceries")) {
      category = "GROCERY";
      merchant = "Demo Grocery Store";
    } else if (textLower.includes("recharge") || textLower.includes("phone")) {
      category = "MOBILE_RECHARGE";
      merchant = "Demo Mobile Recharge";
    } else if (textLower.includes("food") || textLower.includes("dinner") || textLower.includes("tea")) {
      category = "FOOD";
      merchant = "Demo Food Store";
    } else if (textLower.includes("crypto")) {
      category = "CRYPTO";
      merchant = "Demo Crypto";
    } else if (textLower.includes("casino") || textLower.includes("gambling")) {
      category = "GAMBLING";
      merchant = "Demo Casino";
    } else if (textLower.includes("electronics") || textLower.includes("laptop")) {
      category = "SHOPPING";
      merchant = "Demo Electronics";
    }

    const isExplicitSearch = (
      textLower.includes("find") ||
      textLower.includes("search") ||
      textLower.includes("show") ||
      textLower.includes("recommend") ||
      textLower.includes("looking for") ||
      textLower.includes("compare") ||
      textLower.includes("options") ||
      textLower.includes("suggestions")
    );

    const hasPaymentVerb = (
      textLower.includes("pay") ||
      textLower.includes("recharge") ||
      textLower.includes("transfer") ||
      textLower.includes("send") ||
      textLower.includes("buy") ||
      textLower.includes("purchase") ||
      textLower.includes("order") ||
      textLower.includes("direct")
    );

    const isDirectPaymentIntent = amountVal && amountVal > 0 && (hasPaymentVerb || !isExplicitSearch) && !isExplicitSearch;

    if (isDirectPaymentIntent && amountVal && amountVal > 0) {
      setActivityStepIndex(1);
      await new Promise(r => setTimeout(r, 400));

      setActivityStepIndex(2);
      await new Promise(r => setTimeout(r, 400));

      // Invoke Payment Decision Engine
      const decisionRes = await evaluatePaymentDecision({
        amount: amountVal,
        category: category,
        merchant: merchant,
        intent: "PURCHASE",
        userId: user?.user_id || "USER_DEFAULT_001"
      });

      setIsProcessingActivity(false);

      if (decisionRes.decision === "APPROVED") {
        // Execute simulated payment
        const execRes = await initiatePaymentDecision(decisionRes.transaction_id, 'APPROVE', user?.user_id);
        
        const formattedAmt = `₹${amountVal.toLocaleString('en-IN')}`;
        setCompletedTransaction({
          transactionId: decisionRes.transaction_id,
          txId: decisionRes.transaction_id,
          productTitle: `${merchant} Purchase`,
          merchantName: merchant,
          amountPaid: formattedAmt,
          formattedAmount: formattedAmt,
          status: "SUCCESS",
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        });

        setMessages(prev => [...prev, {
          id: `msg-${Date.now() + 1}`,
          sender: 'agent',
          text: `Payment checks passed:\n✓ Delegation active\n✓ Within ₹5,000 transaction limit\n✓ Within monthly budget\n✓ Merchant verified (${merchant})\n✓ Risk acceptable\n\nPayment of ${formattedAmt} executed successfully under UPI Circle delegation.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }]);

        refreshDashboard();
      } else if (decisionRes.decision === "REQUIRES_USER_APPROVAL") {
        setPendingApproval(decisionRes);
        setMessages(prev => [...prev, {
          id: `msg-${Date.now() + 1}`,
          sender: 'agent',
          text: `Payment of ₹${amountVal.toLocaleString('en-IN')} requires your explicit approval before execution.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          isApprovalRequired: true,
          approvalData: decisionRes
        }]);
      } else {
        // DENIED
        setMessages(prev => [...prev, {
          id: `msg-${Date.now() + 1}`,
          sender: 'agent',
          text: `Payment Denied by Payment Decision Engine.\n\nReason: ${decisionRes.reason || 'Policy check failed'} (Code: ${decisionRes.reason_code || 'DENIED'})`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          isDenied: true,
          deniedReason: decisionRes.reason
        }]);
      }

      setIsProcessing(false);
      return;
    }

    // Standard AI Product Search Workflow
    try {
      const result = await sendAgentMessage(userIntentText, user?.user_id);
      setActivityStepIndex(2);
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
        text: "I encountered an issue processing your request. Please try again.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    } finally {
      setIsProcessing(false);
      setIsProcessingActivity(false);
    }
  };

  const handleSelectProduct = (product) => {
    setSelectedProduct(product);
  };

  const handleConfirmPurchase = async (product, totalAmount, options = {}) => {
    const params = {
      product: product,
      amount: totalAmount,
      quoteId: product.id ? `QUOTE_${product.id}` : "QUOTE_MOCK_1001",
      userId: user?.user_id || "USER_DEFAULT_001",
      amountPaise: Math.round(totalAmount * 100),
      upiVpa: options.upiVpa || "sanjay@okicici",
      upiPin: options.upiPin || ""
    };

    const txResult = await purchaseProduct(params);

    if (txResult.success) {
      const formattedAmt = txResult.formattedAmount || `₹${Math.round(totalAmount).toLocaleString('en-IN')}`;
      const txIdVal = txResult.transactionId || `TXN_${Math.floor(1000 + Math.random() * 9000)}`;

      setCompletedTransaction({
        transactionId: txIdVal,
        txId: txIdVal,
        productTitle: product.title || product.name || "Product Item",
        merchantName: product.merchant || product.provider || "Merchant",
        amountPaid: formattedAmt,
        formattedAmount: formattedAmt,
        status: "SUCCESS",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      });

      setSelectedProduct(null);
      refreshDashboard();
    }
    return txResult;
  };

  const handleResetDemo = async () => {
    await resetDemoData(user?.user_id);
    refreshDashboard();
    handleNewChat();
  };

  return (
    <div className="app-layout font-sans">
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

      <main className="app-main-content">
        <header className="top-bar">
          <div className="top-bar-left">
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="btn-icon"
              title="Toggle Menu"
            >
              <Menu size={20} />
            </button>
            <Sparkles className="sparkle-icon" size={20} />
            <span>✦ Intent Guard</span>
          </div>

          <div className="top-bar-actions" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <button
              onClick={() => setShowDashboard(!showDashboard)}
              style={{
                background: 'rgba(37, 99, 235, 0.1)',
                border: '1px solid rgba(37, 99, 235, 0.3)',
                color: '#2563eb',
                padding: '0.35rem 0.75rem',
                borderRadius: '2rem',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              {showDashboard ? 'Hide Dashboard' : 'Show Dashboard'}
            </button>

            <button
              onClick={handleResetDemo}
              title="Development-Only Hackathon Demo Reset"
              style={{
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                color: '#dc2626',
                padding: '0.35rem 0.75rem',
                borderRadius: '2rem',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.25rem'
              }}
            >
              <RefreshCw size={12} />
              <span>Reset Demo</span>
            </button>

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
              <CheckCircle2 size={16} />
              <span>UPI Circle Active</span>
            </button>

            <button onClick={onLockSession} className="btn-lock" title="Lock Session">
              <Lock size={18} />
            </button>

            <button onClick={onLogout || onLockSession} className="btn-lock" title="Log Out">
              <LogOut size={18} style={{ color: '#ef4444' }} />
            </button>
          </div>
        </header>

        {/* Dashboard Banner */}
        {showDashboard && (
          <div style={{ padding: '0 1.5rem' }}>
            <UPICircleDashboard key={dashboardKey} user={user} onOpenSetup={() => setIsUpiModalOpen(true)} />
          </div>
        )}

        <ChatWindow
          messages={messages}
          onSendSuggestion={handleSendIntent}
          isProcessingActivity={isProcessingActivity}
          activityStepIndex={activityStepIndex}
          isActivityComplete={isActivityComplete}
          products={products}
          onSelectProduct={handleSelectProduct}
          completedTransaction={completedTransaction}
          onContinueShopping={() => setCompletedTransaction(null)}
        />

        {/* Render High Risk Approval Card if active */}
        {pendingApproval && (
          <div style={{ padding: '0 1.5rem 1rem 1.5rem' }}>
            <PaymentApprovalCard
              decisionData={pendingApproval}
              onResolved={() => {
                setPendingApproval(null);
                refreshDashboard();
              }}
            />
          </div>
        )}

        <ChatInput
          onSendMessage={handleSendIntent}
          disabled={isProcessing}
        />

        <AuthModal
          isOpen={isAuthModalOpen}
          onClose={() => setIsAuthModalOpen(false)}
          onAuthSuccess={handleAuthSuccess}
        />

        <UPICircleSetupModal
          isOpen={isUpiModalOpen}
          onClose={() => setIsUpiModalOpen(false)}
          user={user}
          onMandateCreated={handleMandateCreated}
        />

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
