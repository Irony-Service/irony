"use client";

import styles from "@/styles/Home.module.css";
import { useCart } from "@/utils/useCart";
import { faPlus } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import Image from "next/image";

export default function CategoryCard({ category }) {
  const { addToCart } = useCart();

  return (
    <div className={styles.categoryCard} data-category={category.title.toLowerCase()}>
      <Image
        src={`/assets/${category.image}`}
        alt={`${category.title}'s Clothing`}
        width={300}
        height={200}
        className={styles.categoryImage}
      />
      <h3>{category.title}</h3>

      <div className={styles.hoverMenu}>
        <ul className={styles.itemsList}>
          {category.items.map((item, index) => (
            <li key={index}>
              <span>{item.name}</span>
              <span>₹{item.price}</span>
              <button className={styles.addBtn} onClick={() => addToCart(item)}>
                <FontAwesomeIcon icon={faPlus} />
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
