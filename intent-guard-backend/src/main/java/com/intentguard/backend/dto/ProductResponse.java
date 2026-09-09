package com.intentguard.backend.dto;

import com.intentguard.backend.model.Intent;
import com.intentguard.backend.model.Product;
import java.util.List;

public class ProductResponse {
    private Intent intent;
    private int totalResults;
    private List<Product> results;

    public ProductResponse() {}

    public ProductResponse(Intent intent, int totalResults, List<Product> results) {
        this.intent = intent;
        this.totalResults = totalResults;
        this.results = results;
    }

    public Intent getIntent() { return intent; }
    public void setIntent(Intent intent) { this.intent = intent; }

    public int getTotalResults() { return totalResults; }
    public void setTotalResults(int totalResults) { this.totalResults = totalResults; }

    public List<Product> getResults() { return results; }
    public void setResults(List<Product> results) { this.results = results; }
}
