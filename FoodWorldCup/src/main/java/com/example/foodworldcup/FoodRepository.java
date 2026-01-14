package com.example.foodworldcup;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface FoodRepository extends JpaRepository<Food, Long> {
    // 기본적으로 제공되는 findAll(), save() 등을 사용하므로
    // 추가 코드가 없어도 작동합니다.
}