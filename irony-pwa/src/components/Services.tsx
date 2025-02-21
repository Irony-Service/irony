"use client";

import styles from "@/styles/Home.module.css";
import { faSprayCan, faTshirt, faWater } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

export default function Services() {
  return (
    <section className={styles.services}>
      <h2>Our Services</h2>
      <div className={styles.serviceGrid}>
        <div className={styles.serviceCard}>
          <FontAwesomeIcon icon={faTshirt} />
          <h3>Ironing</h3>
          <p>Professional pressing for crisp, wrinkle-free garments</p>
        </div>
        <div className={styles.serviceCard}>
          <FontAwesomeIcon icon={faWater} />
          <h3>Washing</h3>
          <p>Advanced washing techniques for all types of fabrics</p>
        </div>
        <div className={styles.serviceCard}>
          <FontAwesomeIcon icon={faSprayCan} />
          <h3>Dry Cleaning</h3>
          <p>Specialized cleaning for delicate materials</p>
        </div>
      </div>
    </section>
  );
}
