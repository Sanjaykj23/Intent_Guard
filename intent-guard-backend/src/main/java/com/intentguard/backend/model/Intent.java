package com.intentguard.backend.model;

import java.util.Map;

/**
 * Intent Model
 * Extracted structured intent parameters parsed from natural language.
 */
public class Intent {
    private String category;
    private String product;
    private String color;
    private String style;
    private String material;
    private Double maxPrice;
    private String deliveryRequirement;
    private Double amount;
    private Map<String, String> extraConstraints;

    public Intent() {}

    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }

    public String getProduct() { return product; }
    public void setProduct(String product) { this.product = product; }

    public String getColor() { return color; }
    public void setColor(String color) { this.color = color; }

    public String getStyle() { return style; }
    public void setStyle(String style) { this.style = style; }

    public String getMaterial() { return material; }
    public void setMaterial(String material) { this.material = material; }

    public Double getMaxPrice() { return maxPrice; }
    public void setMaxPrice(Double maxPrice) { this.maxPrice = maxPrice; }

    public String getDeliveryRequirement() { return deliveryRequirement; }
    public void setDeliveryRequirement(String deliveryRequirement) { this.deliveryRequirement = deliveryRequirement; }

    public Double getAmount() { return amount; }
    public void setAmount(Double amount) { this.amount = amount; }

    public Map<String, String> getExtraConstraints() { return extraConstraints; }
    public void setExtraConstraints(Map<String, String> extraConstraints) { this.extraConstraints = extraConstraints; }
}
