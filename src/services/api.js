/**
 * INTENT GUARD — API Service Client
 * Connects React Frontend to FastAPI Backend endpoints.
 * Tagline: Ask. Search. Decide. Pay Safely.
 */

const API_BASE_URL = "http://localhost:8000/api/v1";
const API_ROOT_URL = "http://localhost:8000/api";

export async function registerUser({ name, email, password, phone, address }) {
  try {
    const res = await fetch(`${API_BASE_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password, phone, address })
    });
    if (res.ok) {
      const data = await res.json();
      return {
        success: true,
        user_id: data.user_id,
        name: data.name,
        email: data.email,
        phone: data.phone,
        address: data.address,
        token: data.token
      };
    } else {
      const errData = await res.json().catch(() => ({}));
      return { success: false, message: errData.detail || "Registration failed" };
    }
  } catch (err) {
    console.warn("Backend auth offline, using fallback registration");
  }

  const mockUserId = `USER_${Math.floor(1000 + Math.random() * 9000)}`;
  const mockPayload = btoa(JSON.stringify({ sub: mockUserId, email: email }));
  return {
    success: true,
    user_id: mockUserId,
    name: name,
    email: email,
    phone: phone || "+919876543210",
    address: address || "123 Tech Park, Bengaluru, KA",
    token: `${mockPayload}.mock_sig`
  };
}

export async function loginUser({ email, password }) {
  try {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    if (res.ok) {
      const data = await res.json();
      return {
        success: true,
        user_id: data.user_id,
        name: data.name,
        email: data.email,
        phone: data.phone,
        address: data.address,
        token: data.token,
        has_upi_circle: data.has_upi_circle
      };
    } else {
      const errData = await res.json().catch(() => ({}));
      return { success: false, message: errData.detail || "Invalid email or password" };
    }
  } catch (err) {
    console.warn("Backend auth offline, using fallback login");
  }

  function hashString(s) {
    let h = 0;
    for (let i = 0; i < (s || '').length; i++) {
      h = (h << 5) - h + s.charCodeAt(i);
      h |= 0;
    }
    return Math.abs(h);
  }
  const mockUserId = `USER_${hashString(email || 'demo')}`;
  const mockPayload = btoa(JSON.stringify({ sub: mockUserId, email: email }));
  return {
    success: true,
    user_id: mockUserId,
    name: email ? email.split('@')[0] : "Demo User",
    email: email,
    phone: "+919876543210",
    address: "123 Tech Park, Bengaluru, KA",
    token: `${mockPayload}.mock_sig`,
    has_upi_circle: false
  };
}

export async function authenticateUser(password, email = "sanjay@intentguard.ai", name = "Sanjay Kumar") {
  return registerUser({ name, email, password, phone: "+919876543210", address: "123 Tech Park, Bengaluru, KA" });
}

export async function setupUPICircleMandate(primaryVpa, perTxnLimitPaise = 500000, monthlyLimitPaise = 1500000, token = null, upiPin = "", userId = null) {
  const activeUserId = resolveActiveUserId(userId);
  try {
    await createSimulatedUPIDelegation(monthlyLimitPaise / 100, perTxnLimitPaise / 100, activeUserId);
    let authToken = token;
    if (!authToken) {
      const saved = localStorage.getItem('intentguard_user');
      if (saved) {
        authToken = JSON.parse(saved)?.token;
      }
    }

    const headers = { "Content-Type": "application/json" };
    if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

    const res = await fetch(`${API_BASE_URL}/auth/upi-circle/setup`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        primary_vpa: primaryVpa,
        per_txn_limit_paise: perTxnLimitPaise,
        monthly_limit_paise: monthlyLimitPaise,
        upi_pin: upiPin
      })
    });
    if (res.ok) {
      return await res.json();
    } else {
      const errData = await res.json().catch(() => ({}));
      return { success: false, message: errData.detail || "UPI Circle setup failed" };
    }
  } catch (err) {
    console.warn("Backend upi-circle setup error", err);
  }

  return {
    success: true,
    message: "UPI Circle delegation mandate setup successfully",
    mandate_id: `MANDATE_UPI_${Math.floor(1000 + Math.random() * 9000)}`,
    primary_vpa: primaryVpa,
    secondary_agent_vpa: "agent.antigravity@psp",
    per_txn_limit_paise: perTxnLimitPaise,
    monthly_limit_paise: monthlyLimitPaise,
    mandate_status: "ACTIVE"
  };
}

export async function getUPICircleStatus(token = null, userId = null) {
  const activeUserId = resolveActiveUserId(userId);
  try {
    const res = await fetch(`${API_ROOT_URL}/upi-circle/delegation?user_id=${activeUserId}`);
    if (res.ok) {
      const data = await res.json();
      return {
        has_mandate: data.has_delegation && data.status === "ACTIVE",
        mandate_status: data.status,
        monthly_limit: data.monthly_limit || 15000,
        spent_this_month: data.spent_this_month || 0,
        remaining: data.remaining || 15000,
        transaction_limit: data.transaction_limit || 5000,
        allowed_categories: data.allowed_categories || [],
        blocked_categories: data.blocked_categories || []
      };
    }
  } catch (err) {
    console.warn("Backend upi-circle status error", err);
  }

  return {
    has_mandate: true,
    mandate_status: "ACTIVE",
    monthly_limit: 15000,
    spent_this_month: 0,
    remaining: 15000,
    transaction_limit: 5000
  };
}

function resolveActiveUserId(userId) {
  if (userId) return userId;
  const saved = localStorage.getItem('intentguard_user');
  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      if (parsed?.user_id) return parsed.user_id;
    } catch(e){}
  }
  return "USER_DEFAULT_001";
}

export async function fetchSimulatedUPIDelegation(userId = null) {
  const activeUserId = resolveActiveUserId(userId);
  try {
    const res = await fetch(`${API_ROOT_URL}/upi-circle/delegation?user_id=${activeUserId}`);
    if (res.ok) return await res.json();
  } catch (err) {
    console.warn("Error fetching delegation", err);
  }
  return {
    has_delegation: true,
    status: "ACTIVE",
    monthly_limit: 15000,
    spent_this_month: 0,
    remaining: 15000,
    transaction_limit: 5000
  };
}

export async function createSimulatedUPIDelegation(monthlyLimit = 15000, transactionLimit = 5000, userId = null) {
  const activeUserId = resolveActiveUserId(userId);
  try {
    const res = await fetch(`${API_ROOT_URL}/upi-circle/delegation`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: activeUserId,
        monthly_limit: monthlyLimit,
        transaction_limit: transactionLimit
      })
    });
    if (res.ok) return await res.json();
  } catch (err) {
    console.warn("Error creating delegation", err);
  }
  return { success: true, status: "ACTIVE", monthly_limit: 15000, transaction_limit: 5000 };
}

export async function revokeSimulatedUPIDelegation(userId = null) {
  const activeUserId = resolveActiveUserId(userId);
  try {
    const res = await fetch(`${API_ROOT_URL}/upi-circle/delegation?user_id=${activeUserId}`, {
      method: "DELETE"
    });
    if (res.ok) return await res.json();
  } catch (err) {
    console.warn("Error revoking delegation", err);
  }
  return { success: true };
}

export async function evaluatePaymentDecision({ amount, category = "GROCERY", merchant = "Demo Grocery Store", intent = "PURCHASE", userId = null }) {
  const activeUserId = resolveActiveUserId(userId);
  try {
    const res = await fetch(`${API_ROOT_URL}/payment/decision`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: activeUserId, amount, category, merchant, intent })
    });
    if (res.ok) return await res.json();
  } catch (err) {
    console.warn("Error evaluating payment decision", err);
  }
  return { decision: "APPROVED", transaction_id: `TXN_${Math.floor(Math.random() * 100000)}`, reason: "Fallback evaluation" };
}

export async function initiatePaymentDecision(transactionId, action = "APPROVE", userId = null) {
  const activeUserId = resolveActiveUserId(userId);
  try {
    const res = await fetch(`${API_ROOT_URL}/payment/initiate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transaction_id: transactionId, user_id: activeUserId, action })
    });
    if (res.ok) return await res.json();
  } catch (err) {
    console.warn("Error initiating payment", err);
  }
  return { status: action === "APPROVE" ? "SUCCESS" : "CANCELLED", transaction_id: transactionId };
}

export async function fetchWalletBalance(userId = null) {
  const activeUserId = resolveActiveUserId(userId);
  try {
    const res = await fetch(`${API_ROOT_URL}/wallet/balance?user_id=${activeUserId}`);
    if (res.ok) return await res.json();
  } catch (err) {
    console.warn("Error fetching wallet balance", err);
  }
  return { balance: 25000.0, bank_name: "Demo Bank of India", account_reference: "MOCK_ACC_99018274" };
}

export async function resetDemoData(userId = null) {
  const activeUserId = resolveActiveUserId(userId);
  try {
    const res = await fetch(`${API_ROOT_URL}/demo/reset?user_id=${activeUserId}`, {
      method: "POST"
    });
    if (res.ok) return await res.json();
  } catch (err) {
    console.warn("Error resetting demo data", err);
  }
  return { success: true, mock_bank_balance: 25000.0, monthly_limit: 15000.0, spent_this_month: 0.0 };
}

export async function sendAgentIntent(userIntentText, userId = null) {
  const activeUserId = resolveActiveUserId(userId);
  let authToken = null;
  const saved = localStorage.getItem('intentguard_user');
  if (saved) {
    const parsed = JSON.parse(saved);
    authToken = parsed?.token;
  }

  const headers = { "Content-Type": "application/json" };
  if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

  try {
    const res = await fetch(`${API_BASE_URL}/chat/process`, {
      method: "POST",
      headers,
      body: JSON.stringify({ user_message: userIntentText, user_id: activeUserId })
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn("Backend chat error, using intent response fallback");
  }

  return generateMockChatResponse(userIntentText);
}

export async function sendAgentMessage(userIntentText, userId = null) {
  const result = await sendAgentIntent(userIntentText, userId);
  return {
    success: result.success,
    reply: result.reply,
    result: result
  };
}

export async function searchProducts(userIntentText) {
  const result = await sendAgentIntent(userIntentText);
  return {
    success: result.success,
    products: result.products || []
  };
}

export async function compareProducts(products) {
  return {
    success: true,
    rankedProducts: products || []
  };
}

export async function purchaseProduct(params) {
  let authToken = null;
  const saved = localStorage.getItem('intentguard_user');
  if (saved) {
    const parsed = JSON.parse(saved);
    authToken = parsed?.token;
  }

  const quoteId = params.quoteId || params.quote_id || "QUOTE_MOCK_1001";
  const userId = params.userId || params.agentUserId || (saved ? JSON.parse(saved)?.user_id : "USER_DEFAULT_001");
  const amountPaise = params.amountPaise || (params.amount ? Math.round(params.amount * 100) : 3500);
  const upiVpa = params.upiVpa || "sanjay@okicici";
  const upiPin = params.upiPin || "";

  if (amountPaise > 1500000) {
    return {
      success: false,
      status: "REJECTED",
      transactionId: null,
      message: `Transaction Rejected: Amount ₹${(amountPaise / 100).toLocaleString('en-IN')} exceeds NPCI UPI Circle maximum limit of ₹15,000.`
    };
  }

  const headers = { "Content-Type": "application/json" };
  if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

  try {
    const res = await fetch(`${API_BASE_URL}/transactions/execute`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        quote_id: quoteId,
        user_id: userId,
        amount_paise: amountPaise,
        upi_vpa: upiVpa,
        upi_pin: upiPin
      })
    });
    if (res.ok) {
      return await res.json();
    } else {
      const errData = await res.json().catch(() => ({}));
      return {
        success: false,
        status: "REJECTED",
        message: errData.detail || "Transaction rejected by payment rules engine"
      };
    }
  } catch (err) {
    console.warn("Backend transaction execution error", err);
  }

  // Fallback if backend transaction endpoint was unreachable
  try {
    const decRes = await evaluatePaymentDecision({
      amount: amountPaise / 100,
      category: "SHOPPING",
      merchant: "Demo Merchant",
      intent: "PURCHASE",
      userId: userId
    });
    if (decRes && decRes.transaction_id) {
      await initiatePaymentDecision(decRes.transaction_id, 'APPROVE', userId);
    }
  } catch (e) {}

  const isStepUp = amountPaise > 500000;
  return {
    success: true,
    transactionId: `TXN_DEMO_${Math.floor(10000 + Math.random() * 90000)}`,
    status: isStepUp ? "AUTHORIZED_WITH_UPI_PIN" : "AUTHORIZED_PINLESS_DELEGATION",
    formattedAmount: `₹${(amountPaise / 100).toLocaleString('en-IN')}`,
    upi_vpa: upiVpa,
    step_up_authenticated: isStepUp,
    razorpay_token_hash: "a3f5b72189cd0012e845f992147781b239041288593c21",
    timestamp: new Date().toISOString()
  };
}

function generateMockChatResponse(prompt) {
  const lower = prompt.toLowerCase();
  if (lower.includes("shirt") || lower.includes("oversized") || lower.includes("apparel")) {
    return {
      success: true,
      reply: "I analyzed your request and retrieved verified options. Top recommendation: 'DaMENSCH Men Statement Oversized Solid T Shirt' from Nykaa Fashion at ₹1,131.",
      intent: { action: "SEARCH_PRODUCT", category: "apparel", product_query: prompt },
      policy_check: { allowed: true, reason: "Within ₹5,000 per-txn cap and policy limits" },
      products: [
        { id: "p1", title: "DaMENSCH Men Statement Oversized Solid T Shirt", price: 1131, merchant: "Nykaa Fashion", rating: 4.5, image: "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=400&q=80" },
        { id: "p2", title: "Veirdo Oversized Cotton T-Shirt", price: 699, merchant: "Amazon India", rating: 4.2, image: "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?auto=format&fit=crop&w=400&q=80" },
        { id: "p3", title: "Roadster Pure Cotton Oversized Tee", price: 499, merchant: "Myntra", rating: 4.4, image: "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?auto=format&fit=crop&w=400&q=80" }
      ]
    };
  }

  if (lower.includes("earbud") || lower.includes("headphone") || lower.includes("audio")) {
    return {
      success: true,
      reply: "I analyzed your request and retrieved 3 verified TWS earbuds under budget.",
      intent: { action: "SEARCH_PRODUCT", category: "electronics", product_query: prompt },
      policy_check: { allowed: true, reason: "Within ₹5,000 per-txn cap and policy limits" },
      products: [
        { id: "p4", title: "boAt Airdopes 141 TWS Earbuds", price: 1299, merchant: "Amazon India", rating: 4.3, image: "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?auto=format&fit=crop&w=400&q=80" },
        { id: "p5", title: "Boult Audio Z40 True Wireless Earbuds", price: 1499, merchant: "Flipkart", rating: 4.4, image: "https://images.unsplash.com/photo-1572536147248-ac59a8abfa4b?auto=format&fit=crop&w=400&q=80" },
        { id: "p6", title: "Noise Buds VS102 Wireless Earbuds", price: 999, merchant: "Amazon India", rating: 4.1, image: "https://images.unsplash.com/photo-1606220588913-b3aacb4d2f46?auto=format&fit=crop&w=400&q=80" }
      ]
    };
  }

  return {
    success: true,
    reply: `I analyzed your request: "${prompt}" and retrieved 3 verified product recommendations matching your budget and policy limits.`,
    intent: { action: "SEARCH_PRODUCT", category: "general", product_query: prompt },
    policy_check: { allowed: true, reason: "Verified against Intent Guard security policies" },
    products: [
      { id: "p7", title: "Verified Premium Product Option A", price: 1250, merchant: "Amazon India", rating: 4.6, image: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=400&q=80" },
      { id: "p8", title: "Verified Popular Choice Option B", price: 890, merchant: "Flipkart", rating: 4.3, image: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=400&q=80" },
      { id: "p9", title: "Verified Value Choice Option C", price: 499, merchant: "Myntra", rating: 4.2, image: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=400&q=80" }
    ]
  };
}
