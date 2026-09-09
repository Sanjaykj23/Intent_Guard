package com.intentguard.backend.model;

import java.util.List;

/**
 * Product Model
 * Represents a normalized marketplace product search result.
 */
public class Product {
    private String id;
    private String name;
    private Double price;
    private Double rating;
    private Integer reviewsCount;
    private String platform;
    private String image; // null if no valid relevant image exists
    private String productUrl;
    private String delivery;
    private String category;
    private String description;
    private List<String> attributes;
    private Integer matchScore;
    private String matchReason;

    public Product() {}

    public Product(String id, String name, Double price, Double rating, Integer reviewsCount,
                   String platform, String image, String productUrl, String delivery,
                   String category, String description, List<String> attributes,
                   Integer matchScore, String matchReason) {
        this.id = id;
        this.name = name;
        this.price = price;
        this.rating = rating;
        this.reviewsCount = reviewsCount;
        this.platform = platform;
        this.image = image;
        this.productUrl = productUrl;
        this.delivery = delivery;
        this.category = category;
        this.description = description;
        this.attributes = attributes;
        this.matchScore = matchScore;
        this.matchReason = matchReason;
    }

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public Double getPrice() { return price; }
    public void setPrice(Double price) { this.price = price; }

    public Double getRating() { return rating; }
    public void setRating(Double rating) { this.rating = rating; }

    public Integer getReviewsCount() { return reviewsCount; }
    public void setReviewsCount(Integer reviewsCount) { this.reviewsCount = reviewsCount; }

    public String getPlatform() { return platform; }
    public void setPlatform(String platform) { this.platform = platform; }

    public String getImage() { return image; }
    public void setImage(String image) { this.image = image; }

    public String getProductUrl() { return productUrl; }
    public void setProductUrl(String productUrl) { this.productUrl = productUrl; }

    public String getDelivery() { return delivery; }
    public void setDelivery(String delivery) { this.delivery = delivery; }

    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public List<String> getAttributes() { return attributes; }
    public void setAttributes(List<String> attributes) { this.attributes = attributes; }

    public Integer getMatchScore() { return matchScore; }
    public void setMatchScore(Integer matchScore) { this.matchScore = matchScore; }

    public String getMatchReason() { return matchReason; }
    public void setMatchReason(String matchReason) { this.matchReason = matchReason; }
}
