package com.intentguard.backend.service;

import com.intentguard.backend.model.Intent;
import org.springframework.stereotype.Service;

import java.util.HashMap;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * IntentService — Rule-based Natural Language Intent Extraction.
 * Converts unstructured user text into a structured Intent object.
 * Architecture allows replacing with LLM / AI parser in production.
 */
@Service
public class IntentService {

    public Intent extractIntent(String userText) {
        if (userText == null) userText = "";
        String text = userText.toLowerCase();

        Intent intent = new Intent();
        intent.setExtraConstraints(new HashMap<>());

        // Category & Product Identification
        if (text.contains("shirt") || text.contains("t-shirt") || text.contains("clothing") || text.contains("dress")) {
            intent.setCategory("clothing");
            intent.setProduct("shirt");
        } else if (text.contains("earbud") || text.contains("headphone") || text.contains("phone") || text.contains("laptop")) {
            intent.setCategory("electronics");
            intent.setProduct(text.contains("earbud") ? "wireless earbuds" : "electronics");
        } else if (text.contains("food") || text.contains("dinner") || text.contains("pizza") || text.contains("restaurant")) {
            intent.setCategory("food");
            intent.setProduct("dinner");
        } else if (text.contains("recharge") || text.contains("mobile") || text.contains("prepaid")) {
            intent.setCategory("mobile_recharge");
            intent.setProduct("mobile recharge");
        } else if (text.contains("fee") || text.contains("college") || text.contains("school") || text.contains("tuition")) {
            intent.setCategory("education_fee");
            intent.setProduct("college fee");
        } else {
            intent.setCategory("general");
            intent.setProduct("transaction");
        }

        // Color extraction
        if (text.contains("black")) intent.setColor("black");
        else if (text.contains("white")) intent.setColor("white");
        else if (text.contains("blue")) intent.setColor("blue");

        // Style extraction
        if (text.contains("oversized")) intent.setStyle("oversized");
        else if (text.contains("slim")) intent.setStyle("slim fit");
        else if (text.contains("relaxed")) intent.setStyle("relaxed fit");

        // Material extraction
        if (text.contains("cotton")) intent.setMaterial("cotton");
        else if (text.contains("linen")) intent.setMaterial("linen");
        else if (text.contains("denim")) intent.setMaterial("denim");

        // Delivery requirement
        if (text.contains("tomorrow")) intent.setDeliveryRequirement("tomorrow");
        else if (text.contains("fast")) intent.setDeliveryRequirement("express");

        // Extract budget / price limits using regex
        Pattern pattern = Pattern.compile("(under|below|less than|for|with)?\\s*₹?\\s*(\\d+)");
        Matcher matcher = pattern.matcher(text);
        if (matcher.find()) {
            try {
                double val = Double.parseDouble(matcher.group(2));
                if ("mobile_recharge".equals(intent.getCategory()) || "education_fee".equals(intent.getCategory())) {
                    intent.setAmount(val);
                } else {
                    intent.setMaxPrice(val);
                }
            } catch (NumberFormatException ignored) {}
        }

        return intent;
    }
}
