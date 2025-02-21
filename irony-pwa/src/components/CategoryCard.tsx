"use client";

import styles from "@/styles/Home.module.css";
import React from "react";

interface CategoryCardProps {
  category: {
    title: string;
    image: string;
    items: Array<{ name: string; price: number }>;
  };
}

const CategoryCard: React.FC<CategoryCardProps> = ({ category }) => {
  return (
    <div className={styles.categoryCard}>
      <img src={category.image} alt={category.title} />
      <h3>{category.title}</h3>
      <ul>
        {Array.isArray(category.items) &&
          category.items.map((item, index) => (
            <li key={index}>
              {item.name} - ₹{item.price}
            </li>
          ))}
      </ul>
    </div>
  );
};

export default CategoryCard;
