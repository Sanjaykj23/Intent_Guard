package com.intentguard.backend.controller;

import com.intentguard.backend.dto.ChatRequest;
import com.intentguard.backend.dto.ProductResponse;
import com.intentguard.backend.model.Intent;
import com.intentguard.backend.model.Product;
import com.intentguard.backend.service.ComparisonService;
import com.intentguard.backend.service.IntentService;
import com.intentguard.backend.service.SearchService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * AgentController
 * Handles marketplace product search, dense embedding similarity comparison, and semantic ranking.
 */
@RestController
@RequestMapping("/api/agent")
public class AgentController {

    private final IntentService intentService;
    private final SearchService searchService;
    private final ComparisonService comparisonService;

    public AgentController(IntentService intentService,
                           SearchService searchService,
                           ComparisonService comparisonService) {
        this.intentService = intentService;
        this.searchService = searchService;
        this.comparisonService = comparisonService;
    }

    @PostMapping("/search")
    public ResponseEntity<ProductResponse> searchAndRank(@Valid @RequestBody ChatRequest request) {
        // 1. Extract Intent
        Intent intent = intentService.extractIntent(request.getMessage());

        // 2. Search Category-Aware Marketplace Products
        List<Product> rawProducts = searchService.searchMarketplaces(intent);

        // 3. Dense Similarity Comparison & Weighted Ranking
        List<Product> rankedProducts = comparisonService.rankAndFilterProducts(rawProducts, intent);

        // 4. Return top ranked results
        List<Product> topResults = rankedProducts.size() > 4 ? rankedProducts.subList(0, 4) : rankedProducts;

        ProductResponse response = new ProductResponse(intent, rawProducts.size(), topResults);
        return ResponseEntity.ok(response);
    }
}
