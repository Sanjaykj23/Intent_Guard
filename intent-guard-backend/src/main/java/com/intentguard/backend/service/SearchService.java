package com.intentguard.backend.service;

import com.intentguard.backend.model.Intent;
import com.intentguard.backend.model.Product;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * SearchService — Marketplace Search System.
 * Prepared for Google Serper API integration via SERPER_API_KEY environment variable.
 * Fallback to Category-Aware Mock Datasets ensuring 100% relevant product images.
 */
@Service
public class SearchService {

    @Value("${serper.api.key:}")
    private String serperApiKey;

    public List<Product> searchMarketplaces(Intent intent) {
        // Future production path: If Serper API key is set, call Google Serper
        if (serperApiKey != null && !serperApiKey.trim().isEmpty()) {
            return searchGoogleSerper(intent);
        }

        // Default: Mock Category-Aware Search
        return searchMockMarketplaces(intent);
    }

    private List<Product> searchGoogleSerper(Intent intent) {
        // Placeholder for HTTP call to Google Serper API
        // https://google.serper.dev/shopping
        return searchMockMarketplaces(intent);
    }

    private List<Product> searchMockMarketplaces(Intent intent) {
        List<Product> products = new ArrayList<>();
        String cat = intent.getCategory() != null ? intent.getCategory().toLowerCase() : "clothing";

        if ("electronics".equals(cat)) {
            products.add(new Product("EARBUDS_001", "SonicPro True Wireless ANC Earbuds", 1899.0, 4.7, 890,
                    "Amazon", "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=600&auto=format&fit=crop&q=80",
                    "https://amazon.in/dp/earbuds1", "Tomorrow by 11 AM", "electronics",
                    "ANC active noise cancellation with 40-hour playback", Arrays.asList("Active Noise Cancellation", "40 Hrs Battery", "Bluetooth 5.3"),
                    97, "Top ANC noise cancellation and 40-hour battery life"));

            products.add(new Product("EARBUDS_002", "BassSurge Stereo Bluetooth Earbuds", 1499.0, 4.5, 430,
                    "Flipkart", "https://images.unsplash.com/photo-1606220588913-b3aacb4d2f46?w=600&auto=format&fit=crop&q=80",
                    "https://flipkart.com/p/earbuds2", "Tomorrow Evening", "electronics",
                    "Deep bass driver with low-latency gaming mode", Arrays.asList("Low Latency 40ms", "30 Hrs Battery", "IPX4"),
                    92, "Deep bass driver with low-latency gaming mode"));

            products.add(new Product("EARBUDS_003", "AirBeat Minimalist Wireless Pods", 1299.0, 4.3, 215,
                    "Myntra", "https://images.unsplash.com/photo-1572536147248-ac59a8abfa4b?w=600&auto=format&fit=crop&q=80",
                    "https://myntra.com/p/earbuds3", "2 Days", "electronics",
                    "Ergonomic lightweight fit with water resistance", Arrays.asList("IPX5 Water Resistant", "24 Hrs Battery"),
                    88, "Ergonomic lightweight fit with IPX5 water resistance"));

        } else if ("food".equals(cat)) {
            products.add(new Product("FOOD_001", "Gourmet Italian Dinner Meal for Two", 749.0, 4.8, 1240,
                    "Swiggy / Zomato", "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=600&auto=format&fit=crop&q=80",
                    "https://swiggy.com/restaurants/gourmet-dinner", "35–45 Mins", "food",
                    "Includes 2 Pastas, Garlic Bread, Dessert & Drinks", Arrays.asList("Italian Cuisine", "Serves 2", "Fresh Ingredients"),
                    98, "Serves 2 with Italian pastas, dessert & drinks"));

            products.add(new Product("FOOD_002", "Artisan Wood-Fired Pizza Combo", 699.0, 4.6, 650,
                    "Zomato", "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600&auto=format&fit=crop&q=80",
                    "https://zomato.com/pizza-combo", "30 Mins", "food",
                    "Large Sourdough Pizza + Potato Wedges", Arrays.asList("Pizza Combo", "Serves 2"),
                    94, "Large sourdough pizza feast for two"));

        } else if ("mobile_recharge".equals(cat)) {
            products.add(new Product("RECHARGE_001", "₹299 Unlimited 5G Prepaid Recharge Plan", 299.0, 4.9, 5400,
                    "Jio / Airtel / Vi", "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=600&auto=format&fit=crop&q=80",
                    "https://jio.com/recharge/299", "Instant Activation", "mobile_recharge",
                    "1.5GB/day 5G data + Unlimited Calls + 100 SMS/day for 28 Days", Arrays.asList("28 Days Validity", "1.5GB/Day + 5G", "Unlimited Voice"),
                    99, "Exact ₹299 28-day 5G prepaid recharge plan"));

        } else if ("education_fee".equals(cat)) {
            products.add(new Product("FEE_001", "Semester College Fee Payment", 25000.0, 5.0, 1,
                    "Direct Institution Portal", "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=600&auto=format&fit=crop&q=80",
                    "https://education.gov.in/fee-portal", "Instant Processing", "education_fee",
                    "Authorized semester fee transfer to verified institution account", Arrays.asList("Institution Verified", "Direct Receipt", "Zero Fee"),
                    99, "Authorized college fee transfer of ₹25,000"));

        } else {
            // Default Clothing / Apparel
            products.add(new Product("SHIRT_001", "Urban Oversized Heavyweight Cotton Shirt", 1299.0, 4.6, 342,
                    "Amazon", "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=600&auto=format&fit=crop&q=80",
                    "https://amazon.in/dp/shirt1", "Tomorrow by 2 PM", "clothing",
                    "100% combed cotton, 240 GSM heavy drop-shoulder silhouette", Arrays.asList("Jet Black", "Oversized Fit", "240 GSM Cotton"),
                    96, "Best overall match for color, oversized fit, and budget"));

            products.add(new Product("SHIRT_002", "Streetwear Drop-Shoulder Dark Cotton Tee", 1449.0, 4.4, 189,
                    "Myntra", "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=600&auto=format&fit=crop&q=80",
                    "https://myntra.com/p/shirt2", "Tomorrow by 8 PM", "clothing",
                    "Bio-washed vintage dark wash finish with double-stitched hems", Arrays.asList("Charcoal Black", "Streetwear Fit", "Bio-Washed"),
                    92, "Premium bio-washed cotton streetwear material"));

            products.add(new Product("SHIRT_003", "Minimalist Casual Loose Cotton Shirt", 1099.0, 4.3, 512,
                    "Flipkart", "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=600&auto=format&fit=crop&q=80",
                    "https://flipkart.com/p/shirt3", "2 Days (Friday)", "clothing",
                    "Breathable cotton blend, ideal for layered casual styling", Arrays.asList("Matte Black", "Loose Fit", "Breathable Cotton"),
                    89, "Great value price for 100% breathable cotton"));

            products.add(new Product("SHIRT_004", "Basic Crew Oversized Daily Shirt", 799.0, 4.1, 94,
                    "Meesho", "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=600&auto=format&fit=crop&q=80",
                    "https://meesho.com/p/shirt4", "3 Days", "clothing",
                    "Lightweight daily-wear cotton tee with simple oversized cut", Arrays.asList("Solid Black", "Basic Oversized"),
                    84, "Budget option well under spending limit"));
        }

        return products;
    }
}
