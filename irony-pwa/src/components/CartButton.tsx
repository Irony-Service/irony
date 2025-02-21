"use client";

import { useCart } from "@/providers/CartProvider"; // Ensure this import is correct
import styles from "@/styles/Home.module.css";
import { faShoppingCart } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useState } from "react";

export default function CartButton() {
  const { cart, clearCart, cartCount } = useCart();
  const [isOpen, setIsOpen] = useState(false);

  const handleWhatsAppOrder = () => {
    if (cart.length === 0) return;

    const items = cart.map((item) => `${item.name} - ₹${item.price}`).join("\n");
    const total = cart.reduce((sum, item) => sum + item.price, 0);
    const message = `Order Summary:\n${items}\n\nTotal: ₹${total}`;

    window.open(`https://wa.me/917416974358?text=${encodeURIComponent(message)}`, "_blank");
    clearCart();
  };

  return (
    <>
      <button onClick={() => setIsOpen(!isOpen)} className={styles.cartButton}>
        <FontAwesomeIcon icon={faShoppingCart} />
        {cartCount > 0 && <span className={styles.cartCount}>{cartCount}</span>}
      </button>

      {isOpen && <div className={styles.cartModal}>{/* Cart modal content */}</div>}
    </>
  );
}
