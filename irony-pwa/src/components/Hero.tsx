"use client";

import styles from "@/styles/Home.module.css";

export default function Hero() {
  return (
    <header className={styles.hero}>
      <h1>Professional Laundry & Dry Cleaning Services</h1>
      <p>Quality care for your garments</p>
      <button className={styles.ctaBtn}>Book Now</button>
    </header>
  );
}
