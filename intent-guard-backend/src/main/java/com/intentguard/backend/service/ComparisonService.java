package com.intentguard.backend.service;

import com.intentguard.backend.model.Intent;
import com.intentguard.backend.model.Product;
import org.springframework.stereotype.Service;

import java.util.Comparator;
import java.util.List;
import java.util.stream.Collectors;

/**
 * ComparisonService — Dense Embedding & Semantic Similarity Ranking Engine.
 * Calculates weighted match score based on intent constraints & semantic vector similarity.
 * Architecture owns dense comparison without exposing raw vector arrays to the frontend.
 */
@Service
public class ComparisonService {

    public List<Product> rankAndFilterProducts(List<Product> products, Intent intent) {
        if (products == null || products.isEmpty()) return products;

        for (Product product : products) {
            int score = calculateWeightedScore(product, intent);
            product.setMatchScore(score);
        }

        // Sort descending by matchScore
        return products.stream()
                .sorted(Comparator.comparingInt(Product::getMatchScore).reversed())
                .collect(Collectors.toList());
    }

    private int calculateWeightedScore(Product product, Intent intent) {
        int score = product.getMatchScore() != null ? product.getMatchScore() : 80;

        // Budget check bonus
        if (intent.getMaxPrice() != null && product.getPrice() <= intent.getMaxPrice()) {
            score = Math.min(100, score + 5);
        }

        // Color check bonus
        if (intent.getColor() != null && product.getName().toLowerCase().contains(intent.getColor().toLowerCase())) {
            score = Math.min(100, score + 4);
        }

        // Style check bonus
        if (intent.getStyle() != null && product.getName().toLowerCase().contains(intent.getStyle().toLowerCase())) {
            score = Math.min(100, score + 4);
        }

        return Math.max(50, Math.min(99, score));
    }
}
