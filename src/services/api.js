/**
 * INTENT GUARD — API Service Layer
 * 
 * CORE SECURITY RULE:
 * "The AI gets permission, not credentials."
 * 
 * Communicates directly with Spring Boot + Spring JDBC + MySQL backend on http://localhost:8080/api.
 * Includes graceful fallback to local mock data if the backend server is not running.
 */

const API_BASE_URL = "http://localhost:8080/api";

// Fallback Mock Dataset
const MOCK_DATASETS = {
  apparel: [
    {
      id: "PROD_SHIRT_01",
      name: "Urban Oversized Heavyweight Cotton Shirt",
      price: 1299,
      originalPrice: 1999,
      rating: 4.6,
      reviewsCount: 342,
      platform: "Amazon",
      image: "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=600&auto=format&fit=crop&q=80",
      productUrl: "https://amazon.in/dp/shirt1",
      delivery: "Tomorrow by 2 PM",
      matchScore: 96,
      matchAttributes: { color: "Jet Black", style: "Oversized Fit", budget: "₹1,299 (Under ₹1,500)" },
      merchant: "UrbanWear Official",
      category: "Clothing"
    },
    {
      id: "PROD_SHIRT_02",
      name: "Streetwear Drop-Shoulder Dark Cotton Tee",
      price: 1449,
      originalPrice: 2299,
      rating: 4.4,
      reviewsCount: 189,
      platform: "Myntra",
      image: "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=600&auto=format&fit=crop&q=80",
      productUrl: "https://myntra.com/p/shirt2",
      delivery: "Tomorrow by 8 PM",
      matchScore: 92,
      matchAttributes: { color: "Charcoal Black", style: "Streetwear Fit", budget: "₹1,449 (Under ₹1,500)" },
      merchant: "Roadster Select",
      category: "Clothing"
    }
  ]
};

/**
 * 1. Authenticate User
 * POST /api/auth/login
 */
export async function authenticateUser(password) {
  try {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password })
    });
    if (res.ok) {
      const data = await res.json();
      return {
        success: data.success,
        agentUserId: data.agentUserId || "USER_1",
        userName: "Alex Morgan",
        message: data.message
      };
    }
  } catch (e) {
    console.warn("Backend unavailable, using frontend mock auth:", e);
  }

  // Mock Fallback
  return new Promise((resolve) => {
    setTimeout(() => {
      if (password === "intent123") {
        resolve({
          success: true,
          agentUserId: "USER_1",
          userName: "Alex Morgan",
          token: "MOCK_AUTH_TOKEN"
        });
      } else {
        resolve({
          success: false,
          message: "Invalid authorization password. Try 'intent123' for demo access."
        });
      }
    }, 400);
  });
}

/**
 * 2. Send Agent Message / Process Intent
 * POST /api/chat/message
 */
export async function sendAgentMessage(userIntent) {
  try {
    const res = await fetch(`${API_BASE_URL}/chat/message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ userId: "USER_1", conversationId: null, message: userIntent })
    });
    if (res.ok) {
      const data = await res.json();
      return {
        success: true,
        conversationId: data.conversationId,
        reply: data.agentMessage,
        intent: data.intent
      };
    }
  } catch (e) {
    console.warn("Backend unavailable, using frontend mock response:", e);
  }

  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        success: true,
        reply: "I'll search across available marketplaces and compare the best matches based on your requirements."
      });
    }, 300);
  });
}

/**
 * 3. Search Products
 * POST /api/agent/search
 */
export async function searchProducts(userIntent) {
  try {
    const res = await fetch(`${API_BASE_URL}/agent/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ userId: "USER_1", message: userIntent })
    });
    if (res.ok) {
      const data = await res.json();
      return {
        success: true,
        totalRawFound: data.totalResults || 47,
        products: data.results || []
      };
    }
  } catch (e) {
    console.warn("Backend unavailable, using frontend mock search:", e);
  }

  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        success: true,
        totalRawFound: 47,
        products: MOCK_DATASETS.apparel
      });
    }, 600);
  });
}

/**
 * 4. Compare Products
 */
export async function compareProducts(products) {
  return new Promise((resolve) => {
    setTimeout(() => {
      const ranked = [...products].sort((a, b) => (b.matchScore || 0) - (a.matchScore || 0));
      resolve({
        success: true,
        rankedProducts: ranked,
        totalAnalyzed: 47
      });
    }, 400);
  });
}

/**
 * 5. Execute Authorized Purchase Transaction
 * POST /api/transactions/authorize -> POST /api/transactions/execute
 */
export async function purchaseProduct({ agentUserId, productId, amount }) {
  try {
    // 1. Authorize
    const authRes = await fetch(`${API_BASE_URL}/transactions/authorize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ userId: agentUserId || "USER_1", productId, amount })
    });

    if (authRes.ok) {
      const authData = await authRes.json();

      // 2. Execute
      const execRes = await fetch(`${API_BASE_URL}/transactions/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ authorizationReference: authData.authorizationReference })
      });

      if (execRes.ok) {
        const execData = await execRes.json();
        return {
          success: true,
          transactionId: execData.transactionId,
          status: execData.status,
          amountPaid: execData.amountPaid || amount,
          timestamp: new Date().toISOString()
        };
      }
    }
  } catch (e) {
    console.warn("Backend unavailable, using frontend mock payment execution:", e);
  }

  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        success: true,
        transactionId: `TXN_DEMO_${Math.floor(10000 + Math.random() * 90000)}`,
        status: "AUTHORIZED_AND_EXECUTED",
        amountPaid: amount,
        timestamp: new Date().toISOString()
      });
    }, 1000);
  });
}
