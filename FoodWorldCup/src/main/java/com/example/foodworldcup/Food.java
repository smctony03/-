package com.example.foodworldcup;

import jakarta.persistence.*;

@Entity
@Table(name = "foods")
public class Food {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String name;



    @Column(name = "image_url")
    private String imgUrl;

    private String country;        // 한식, 중식..
    private String taste;          // 담백한 맛, 자극적인 맛..

    // 자바: mainIngredient <-> DB: main_ingredient
    @Column(name = "main_ingredient")
    private String mainIngredient;

    private String temperature;    // 따듯한 것, 차가운 것..

    // 자바: cookingType <-> DB: cooking_type
    @Column(name = "cooking_type")
    private String cookingType;

    // ================= Getter & Setter =================

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getImgUrl() {
        return imgUrl;
    }

    public void setImgUrl(String imgUrl) {
        this.imgUrl = imgUrl;
    }

    public String getCountry() {
        return country;
    }

    public void setCountry(String country) {
        this.country = country;
    }

    public String getTaste() {
        return taste;
    }

    public void setTaste(String taste) {
        this.taste = taste;
    }

    public String getMainIngredient() {
        return mainIngredient;
    }

    public void setMainIngredient(String mainIngredient) {
        this.mainIngredient = mainIngredient;
    }

    public String getTemperature() {
        return temperature;
    }

    public void setTemperature(String temperature) {
        this.temperature = temperature;
    }

    public String getCookingType() {
        return cookingType;
    }

    public void setCookingType(String cookingType) {
        this.cookingType = cookingType;
    }
}