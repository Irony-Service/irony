import config from "@/config/config";
import styles from "@/styles/Home.module.css";

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.footerContent}>
        <div className={styles.footerSection}>
          <h3>Contact Us</h3>
          <p>Email: {config.contact.email}</p>
          <p>Phone: {config.contact.phone}</p>
        </div>
        <div className={styles.footerSection}>
          <h3>Operating Hours</h3>
          <p>{config.businessHours.weekdays}</p>
          <p>{config.businessHours.sunday}</p>
        </div>
        <div className={styles.footerSection}>
          <h3>Areas We Serve</h3>
          <div className={styles.areasGrid}>
            {config.operatingAreas.areas.map((area) => (
              <span key={area} className={styles.areaTag}>
                {area}
              </span>
            ))}
          </div>
          <p className={styles.mt2}>
            {config.operatingAreas.city}, {config.operatingAreas.state}
          </p>
        </div>
      </div>
      <div className={styles.footerBottom}>
        <p>
          &copy; {config.company.year} {config.company.name}. All rights reserved.
        </p>
      </div>
    </footer>
  );
}
