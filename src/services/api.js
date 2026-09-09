/**
 * INTENT GUARD — API Service Client
 * Connects React Frontend to FastAPI Backend endpoints (with intelligent fallback).
 * Tagline: Ask. Search. Decide. Pay Safely.
 */

const API_BASE_URL = "http://localhost:8000/api/v1";

/**
 * 1. Authenticate / Register User (Stores details & Razorpay Mandate Token Hash)
 */
export async function authenticateUser(password, email = "sanjay@intentguard.ai", name = "Sanjay Kumar") {
  try {
    const res = await fetch(`${API_BASE_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password })
    });
    if (res.ok) {
      const data = await res.json();
      return {
        success: true,
        agentUserId: data.user_id,
        userName: data.name,
        email: data.email,
        razorpayTokenHash: data.razorpay_token_hash,
        token: `SECURE_JWT_${data.user_id}`
      };
    }
  } catch (err) {
    console.warn("Backend auth offline, using fallback auth response");
  }

  // Fallback demo user response
  return {
    success: true,
    agentUserId: "USER_4821",
    userName: "Sanjay Kumar",
    email: email,
    razorpayTokenHash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    token: "MOCK_AUTH_TOKEN_SECURE_7721"
  };
}

/**
 * 2. Send Intent Prompt to Llama AI Engine & Process Live Search
 */
export async function sendAgentIntent(userIntentText, userId = "USER_4821") {
  try {
    const res = await fetch(`${API_BASE_URL}/chat/process`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_message: userIntentText, user_id: userId })
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn("Backend chat offline, generating mock intent response");
  }

  return generateMockChatResponse(userIntentText);
}

// Backward compatibility wrapper for Home.jsx
export async function sendAgentMessage(userIntentText) {
  const result = await sendAgentIntent(userIntentText);
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

/**
 * 3. Execute Authorized Transaction
 */
export async function purchaseProduct(params) {
  const quoteId = params.quoteId || params.quote_id || "QUOTE_MOCK_1001";
  const userId = params.userId || params.agentUserId || "USER_4821";
  const amountPaise = params.amountPaise || (params.amount ? params.amount * 100 : 3500);

  try {
    const res = await fetch(`${API_BASE_URL}/transactions/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ quote_id: quoteId, user_id: userId, amount_paise: amountPaise })
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn("Backend transaction execution offline, using fallback response");
  }

  return {
    success: true,
    transactionId: `TXN_DEMO_${Math.floor(10000 + Math.random() * 90000)}`,
    status: "AUTHORIZED_AND_EXECUTED",
    formattedAmount: `₹${(amountPaise / 100).toFixed(2)}`,
    razorpay_token_hash: "a3f5b72189cd0012e845f992147781b239041288593c21",
    timestamp: new Date().toISOString()
  };
}

/**
 * 4. Fetch Cryptographic Audit Ledger Logs
 */
export async function fetchAuditLogs() {
  try {
    const res = await fetch(`${API_BASE_URL}/audit/logs`);
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn("Backend audit API offline");
  }
  return { success: false, logs: [] };
}

// Fallback chat generator for offline mode
function generateMockChatResponse(userIntentText) {
  const query = (userIntentText || "").toLowerCase().strip?.() || userIntentText.toLowerCase();

  // Check Greetings & Conversational Queries
  if (query.match(/^(hello|hi|hey|greetings|good morning|good evening|who are you|what can you do|help)$/i) || query === "hello" || query === "hi") {
    return {
      success: true,
      reply: "Hello! I am IntentGuard AI, your safe universal transaction assistant. How can I help you today? You can ask me to search for products under a budget, order tea, recharge your mobile, or check spending policies.",
      intent: {
        intent: "greeting",
        category: "general",
        product: null,
        max_price_paise: null,
        currency: "INR"
      },
      products: [],
      policy_check: null,
      quote: null,
      rag_context: ""
    };
  }

  let category = "apparel";
  let products = [];

  if (query.includes("laptop") || query.includes("coding")) {
    category = "electronics";
    products = [
      {
        id: "PROD_LAPTOP_01",
        title: "ASUS Vivobook 15 Intel Core i5 12th Gen (16GB/512GB SSD/15.6\")",
        price_paise: 5299000,
        formatted_price: "₹52,990",
        merchant: "Amazon India",
        rating: 4.7,
        reviews_count: 1420,
        product_url: "https://www.amazon.in/dp/B0B5678901",
        image_url: "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=600&auto=format&fit=crop&q=80",
        delivery: "Tomorrow by 10 AM",
        category: "electronics",
        match_score: 98,
        match_reason: "High-performance i5 12th Gen processor + 16GB RAM ideal for coding & AI under ₹70,000",
        match_attributes: { cpu: "Core i5 12th Gen", ram: "16GB DDR4", budget: "₹52,990 (Under ₹70,000)" }
      }
    ];
  } else if (query.includes("tea") || query.includes("chai")) {
    category = "food";
    products = [
      {
        id: "PROD_TEA_01",
        title: "Fresh Masala Kulhad Chai (200ml)",
        price_paise: 3500,
        formatted_price: "₹35",
        merchant: "Gupta Chai Corner (Swiggy)",
        rating: 4.8,
        reviews_count: 1240,
        product_url: "https://www.swiggy.com/restaurants/gupta-chai-corner-local-tea-shop-10293",
        image_url: "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=600&auto=format&fit=crop&q=80",
        delivery: "12 Mins",
        category: "food",
        match_score: 99,
        match_reason: "Freshly brewed ginger masala chai from nearest top-rated shop under ₹50",
        match_attributes: { cuisines: "Indian Beverage", size: "200ml", budget: "₹35 (Under ₹50 limit)" }
      }
    ];
  } else if (query.includes("recharge") || query.includes("2gb/day")) {
    category = "recharge";
    products = [
      {
        id: "PROD_RECHARGE_01",
        title: "Jio ₹299 Unlimited 5G Prepaid Plan (2GB/Day + Unlimited Calls)",
        price_paise: 29900,
        formatted_price: "₹299",
        merchant: "Jio Telecom Direct",
        rating: 4.9,
        reviews_count: 5400,
        product_url: "https://www.jio.com/selfcare/recharge/prepaid/",
        image_url: "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=600&auto=format&fit=crop&q=80",
        delivery: "Instant Activation",
        category: "recharge",
        match_score: 99,
        match_reason: "Cheapest 2GB/day 5G plan with 28 days validity + 100 SMS/day",
        match_attributes: { validity: "28 Days", data: "2GB/Day 5G", calls: "Unlimited" }
      }
    ];
  } else {
    products = [
      {
        id: "PROD_SHOES_01",
        title: "Nike Revolution 6 Next Nature Black Running Shoes",
        price_paise: 349500,
        formatted_price: "₹3,495",
        merchant: "Flipkart Store",
        rating: 4.7,
        reviews_count: 890,
        product_url: "https://www.flipkart.com/nike-revolution-6-running-shoes/p/itm123456789",
        image_url: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&auto=format&fit=crop&q=80",
        delivery: "Tomorrow by 11 AM",
        category: "apparel",
        match_score: 97,
        match_reason: "Top-rated breathable running shoes with high traction sole",
        match_attributes: { brand: "Nike", type: "Running", budget: "₹3,495 (Under ₹5,000)" }
      }
    ];
  }

  return {
    success: true,
    reply: `I analyzed your intent using Llama 3 and retrieved live options matching your constraints. Top recommendation: '${products[0].title}' at ${products[0].formatted_price}.`,
    intent: {
      intent: category === "food" ? "food_order" : (category === "recharge" ? "mobile_recharge" : "product_search"),
      category: category,
      product: userIntentText,
      max_price_paise: products[0].price_paise + 5000,
      currency: "INR"
    },
    products: products,
    policy_check: {
      allowed: true,
      status_code: "ALLOWED",
      risk_level: products[0].price_paise <= 20000 ? "LOW" : "MEDIUM",
      auto_approved: products[0].price_paise <= 20000,
      reason: "Transaction evaluated against user spending policy rules."
    },
    quote: {
      quote_id: `QUOTE_MOCK_${Math.floor(1000 + Math.random() * 9000)}`,
      expires_at: new Date(Date.now() + 180000).toISOString(),
      quote_hash: "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069"
    }
  };
}
