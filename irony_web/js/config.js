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
    defaultMessage: "Hi, I would like to book a laundry service",
  },

  // Service Provider Portal
  serviceProvider: {
    loginUrl: "https://ironystore.in/login",
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
};

export default config;
