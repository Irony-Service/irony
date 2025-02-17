const config = {
  // Contact Information
  contact: {
    email: "support@ironystore.in",
    phone: "+917416974358",
    whatsappNumber: "917416974358", // Without '+' prefix
  },

  // Business Hours
  businessHours: {
    weekdays: "Monday - Saturday: 8AM - 9PM",
    sunday: "Sunday: 8AM - 9PM",
  },

  // WhatsApp Configuration
  whatsapp: {
    defaultMessage: "Hi Irony",
  },

  // Service Provider Portal
  serviceProvider: {
    loginUrl: "https://ironystore.in/service/home/agent",
  },

  // Company Information
  company: {
    name: "Irony Laundromat",
    year: new Date().getFullYear(),
  },

  // Operating Areas in Hyderabad
  operatingAreas: {
    areas: [
      "Madhapur",
      "Gachibowli",
      "HITEC City",
      "Kondapur",
      "Jubilee Hills",
      "Banjara Hills",
      "Kukatpally",
      "Miyapur",
      "Manikonda",
      "Financial District",
    ],
    city: "Hyderabad",
    state: "Telangana",
  },

  // Categories and Items
  categories: {
    men: [
      { name: "Shirt", price: 60 },
      { name: "Pant", price: 80 },
      { name: "Suit", price: 300 },
      { name: "Blazer", price: 200 },
    ],
    women: [
      { name: "Saree", price: 200 },
      { name: "Suit", price: 150 },
      { name: "Dress", price: 180 },
      { name: "Blouse", price: 70 },
    ],
    kids: [
      { name: "Shirt", price: 40 },
      { name: "Pant", price: 50 },
      { name: "Dress", price: 80 },
      { name: "Uniform", price: 100 },
    ],
    bedding: [
      { name: "Bedsheet", price: 150 },
      { name: "Blanket", price: 250 },
      { name: "Pillow Cover", price: 40 },
      { name: "Duvet", price: 400 },
    ],
  },
};

export default config;
