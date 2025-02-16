import config from "./config.js";

// WhatsApp button click handler
document.getElementById("whatsappBtn").addEventListener("click", () => {
  const whatsappUrl = `https://wa.me/${config.contact.whatsappNumber}`;
  window.open(whatsappUrl, "_blank");
});

// Provider button click handler
document.getElementById("providerBtn").addEventListener("click", () => {
  window.location.href = config.serviceProvider.loginUrl;
});

// Book Now button handler
document.querySelector(".cta-btn").addEventListener("click", () => {
  const whatsappUrl = `https://wa.me/${config.contact.whatsappNumber}?text=${encodeURIComponent(
    config.whatsapp.defaultMessage
  )}`;
  window.open(whatsappUrl, "_blank");
});

// Add smooth scrolling for better user experience
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault();
    document.querySelector(this.getAttribute("href")).scrollIntoView({
      behavior: "smooth",
    });
  });
});

// Add simple animation on scroll
window.addEventListener("scroll", () => {
  const elements = document.querySelectorAll(".service-card, .category-card");
  elements.forEach((element) => {
    const position = element.getBoundingClientRect();
    if (position.top < window.innerHeight) {
      element.style.opacity = "1";
      element.style.transform = "translateY(0)";
    }
  });
});
