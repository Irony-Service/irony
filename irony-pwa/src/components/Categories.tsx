"use client";

import config from "@/config/config";
import styles from "@/styles/Home.module.css";
import CategoryCard from "./CategoryCard"; // Ensure this import is correct

export default function Categories() {
  return (
    <section className={styles.categories}>
      <h2>Services For</h2>
      <div className={styles.categoryGrid}>
        {Object.entries(config.categories).map(([key, items]) => (
          <CategoryCard
            key={key}
            category={{
              title: key.charAt(0).toUpperCase() + key.slice(1),
              image: `${key}.webp`,
              items: Array.isArray(items) ? items : [], // Ensure items is an array
            }}
          />
        ))}
      </div>
    </section>
  );
}
