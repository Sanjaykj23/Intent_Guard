/**
 * INTENT GUARD — API Service (Mock Architecture)
 * 
 * CORE ARCHITECTURAL PRINCIPLE:
 * "The AI gets permission, not credentials."
 * 
 * The AI knows the transaction amount, product details, and intent constraints.
 * The AI NEVER knows or accesses the user's private financial bank balance.
 */

// Category Datasets with Verified Relevant Product Images
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
      productUrl: "https://amazon.in/dp/example1",
      delivery: "Tomorrow by 2 PM",
      matchScore: 96,
      matchReason: "Best overall match for color, oversized fit, and budget",
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
      productUrl: "https://myntra.com/p/example2",
      delivery: "Tomorrow by 8 PM",
      matchScore: 92,
      matchReason: "Premium bio-washed cotton material",
      matchAttributes: { color: "Charcoal Black", style: "Streetwear Fit", budget: "₹1,449 (Under ₹1,500)" },
      merchant: "Roadster Select",
      category: "Clothing"
    },
    {
      id: "PROD_SHIRT_03",
      name: "Minimalist Casual Loose Cotton Shirt",
      price: 1099,
      originalPrice: 1699,
      rating: 4.3,
      reviewsCount: 512,
      platform: "Flipkart",
      image: "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=600&auto=format&fit=crop&q=80",
      productUrl: "https://flipkart.com/p/example3",
      delivery: "2 Days (Friday)",
      matchScore: 89,
      matchReason: "Great value price for 100% breathable cotton",
      matchAttributes: { color: "Matte Black", style: "Loose Fit", budget: "₹1,099 (Under ₹1,500)" },
      merchant: "Highlander Store",
      category: "Clothing"
    },
    {
      id: "PROD_SHIRT_04",
      name: "Basic Crew Oversized Daily Shirt",
      price: 799,
      originalPrice: 1299,
      rating: 4.1,
      reviewsCount: 94,
      platform: "Meesho",
      image: "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=600&auto=format&fit=crop&q=80",
      productUrl: "https://meesho.com/p/example4",
      delivery: "3 Days",
      matchScore: 84,
      matchReason: "Budget option well under spending limit",
      matchAttributes: { color: "Solid Black", style: "Basic Oversized", budget: "₹799 (Well under budget)" },
      merchant: "Trends Hub",
      category: "Clothing"
    }
  ],

  electronics: [
    {
      id: "PROD_EARBUDS_01",
      name: "SonicPro True Wireless ANC Earbuds",
      price: 1899,
      originalPrice: 3499,
      rating: 4.7,
      reviewsCount: 890,
      platform: "Amazon",
      image: "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=600&auto=format&fit=crop&q=80",
      productUrl: "https://amazon.in/dp/earbuds1",
      delivery: "Tomorrow by 11 AM",
      matchScore: 97,
      matchReason: "Top ANC noise cancellation and 40-hour playback",
      matchAttributes: { feature: "Active Noise Cancellation", battery: "40 Hrs", budget: "₹1,899 (Under ₹2,000)" },
      merchant: "Sonic Audio Official",
      category: "Electronics"
    },
    {
      id: "PROD_EARBUDS_02",
      name: "BassSurge Stereo Bluetooth Earbuds",
      price: 1499,
      originalPrice: 2499,
      rating: 4.5,
      reviewsCount: 430,
      platform: "Flipkart",
      image: "https://images.unsplash.com/photo-1606220588913-b3aacb4d2f46?w=600&auto=format&fit=crop&q=80",
      productUrl: "https://flipkart.com/p/earbuds2",
      delivery: "Tomorrow Evening",
      matchScore: 91,
      matchReason: "Deep bass driver with low-latency gaming mode",
      matchAttributes: { feature: "Low Latency 40ms", battery: "30 Hrs", budget: "₹1,499 (Under ₹2,000)" },
      merchant: "Boat Electronics",
      category: "Electronics"
    },
    {
      id: "PROD_EARBUDS_03",
      name: "AirBeat Minimalist Wireless Pods",
      price: 1299,
      originalPrice: 1999,
      rating: 4.3,
      reviewsCount: 215,
      platform: "Myntra",
      image: "https://images.unsplash.com/photo-1572536147248-ac59a8abfa4b?w=600&auto=format&fit=crop&q=80",
      productUrl: "https://myntra.com/p/earbuds3",
      delivery: "2 Days",
      matchScore: 86,
      matchReason: "Ergonomic lightweight fit with IPX5 water resistance",
      matchAttributes: { feature: "IPX5 Water Resistant", battery: "24 Hrs", budget: "₹1,299 (Under ₹2,000)" },
      merchant: "Noise Store",
      category: "Electronics"
    }
  ],

  food: [
    {
      id: "PROD_FOOD_01",
      name: "Gourmet Italian Dinner Meal for Two",
      price: 749,
      originalPrice: 999,
      rating: 4.8,
      reviewsCount: 1240,
      platform: "Swiggy / Zomato",
      image: "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=600&auto=format&fit=crop&q=80",
      productUrl: "https://swiggy.com/restaurants/gourmet-dinner",
      delivery: "35–45 Mins",
      matchScore: 98,
      matchReason: "Includes 2 Pastas, Garlic Bread, Dessert & Drinks",
      matchAttributes: { cuisine: "Italian Feast", portions: "Serves 2", budget: "₹749 (Under ₹800)" },
      merchant: "Trattoria Bella",
      category: "Food"
    },
    {
      id: "PROD_FOOD_02",
      name: "Artisan Wood-Fired Pizza Combo",
      price: 699,
      originalPrice: 899,
      rating: 4.6,
      reviewsCount: 650,
      platform: "Zomato",
      image: "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600&auto=format&fit=crop&q=80",
      productUrl: "https://zomato.com/pizza-combo",
      delivery: "30 Mins",
      matchScore: 93,
      matchReason: "Large Sourdough Pizza + Potato Wedges",
      matchAttributes: { cuisine: "Pizza Combo", portions: "Serves 2", budget: "₹699 (Under ₹800)" },
      merchant: "Crust & Oven",
      category: "Food"
    }
  ],

  recharge: [
    {
      id: "PROD_RECHARGE_01",
      name: "₹299 Unlimited 5G Prepaid Recharge Plan",
      price: 299,
      originalPrice: 299,
      rating: 4.9,
      reviewsCount: 5400,
      platform: "Jio / Airtel / Vi",
      image: "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=600&auto=format&fit=crop&q=80",
      productUrl: "https://jio.com/recharge/299",
      delivery: "Instant Activation",
      matchScore: 99,
      matchReason: "1.5GB/day 5G data + Unlimited Calls + 100 SMS/day",
      matchAttributes: { validity: "28 Days", data: "1.5GB/Day + Unlimited 5G", budget: "Exact ₹299 match" },
      merchant: "Telecom Provider Direct",
      category: "Recharge"
    }
  ]
};

/**
 * 1. Authenticate User (DEMO ONLY)
 * Replace with Spring Boot backend API before production.
 */
export async function authenticateUser(password) {
  return new Promise((resolve) => {
    setTimeout(() => {
      if (password === "intent123") {
        resolve({
          success: true,
          agentUserId: "USER_4821",
          userName: "Alex Morgan",
          token: "MOCK_AUTH_TOKEN_SECURE_7721"
        });
      } else {
        resolve({
          success: false,
          message: "Invalid authorization password. Please try 'intent123' for demo access."
        });
      }
    }, 500);
  });
}

/**
 * 2. Send Agent Message / Intent Analysis
 */
export async function sendAgentMessage(userIntent) {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        success: true,
        reply: "I'll search across available marketplaces and compare the best matches based on your requirements."
      });
    }, 350);
  });
}

/**
 * 3. Search Products (Category-Aware Intent Search)
 * Frontend mock inspecting intent keywords to return relevant products.
 */
export async function searchProducts(userIntent) {
  const query = (userIntent || "").toLowerCase();

  return new Promise((resolve) => {
    setTimeout(() => {
      let matchedCategory = "apparel";

      if (query.includes("earbud") || query.includes("headphone") || query.includes("phone") || query.includes("electronics") || query.includes("wireless")) {
        matchedCategory = "electronics";
      } else if (query.includes("food") || query.includes("dinner") || query.includes("pizza") || query.includes("restaurant") || query.includes("meal")) {
        matchedCategory = "food";
      } else if (query.includes("recharge") || query.includes("mobile") || query.includes("plan") || query.includes("telecom")) {
        matchedCategory = "recharge";
      }

      const products = MOCK_DATASETS[matchedCategory] || MOCK_DATASETS.apparel;

      resolve({
        success: true,
        totalRawFound: 47,
        products: products
      });
    }, 700);
  });
}

/**
 * 4. Compare Products using Semantic Matching
 */
export async function compareProducts(products) {
  return new Promise((resolve) => {
    setTimeout(() => {
      const ranked = [...products].sort((a, b) => b.matchScore - a.matchScore);
      resolve({
        success: true,
        rankedProducts: ranked,
        totalAnalyzed: 47
      });
    }, 600);
  });
}

/**
 * 5. Purchase Product / Execute Authorized Transaction
 * Accepts safe identifiers ONLY. Never receives or stores bank balances or credentials.
 */
export async function purchaseProduct({ agentUserId, productId, amount }) {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        success: true,
        transactionId: `TXN_DEMO_${Math.floor(10000 + Math.random() * 90000)}`,
        status: "AUTHORIZED_AND_EXECUTED",
        amountPaid: amount,
        timestamp: new Date().toISOString(),
        paymentAuthorizationRef: `AUTH_REF_${Math.floor(100000 + Math.random() * 900000)}`
      });
    }, 1100);
  });
}
