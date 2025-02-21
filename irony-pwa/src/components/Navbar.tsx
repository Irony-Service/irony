"use client";

import styles from "@/styles/Home.module.css";

export default function Navbar() {
  return (
    <nav className={styles.navbar}>
      <div className={styles.logo} id="companyName">
        <i className="fas fa-steam logo-icon"></i>
        <span className="logo-text">Irony Laundromat</span>
      </div>
      <div className={styles.navButtons}>
        <button id="whatsappBtn" className={styles.contactBtn}>
          <i className="fab fa-whatsapp"></i> Book Service
        </button>
        <button id="providerBtn" className={styles.providerBtn}>
          Service Provider Login
        </button>
      </div>
    </nav>
  );
}
