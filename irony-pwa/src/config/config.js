export default {
  company: {
    name: "Irony Laundromat",
    year: new Date().getFullYear(),
  },
  contact: {
    email: "info@ironylaundromat.com",
    phone: "+91 7416974358",
    whatsappNumber: "917416974358",
  },
  businessHours: {
    weekdays: "Mon-Sat: 9:00 AM - 8:00 PM",
    sunday: "Sunday: 10:00 AM - 6:00 PM",
  },
  operatingAreas: {
    city: "Bangalore",
    state: "Karnataka",
    areas: ["Koramangala", "HSR Layout", "BTM Layout", "Indiranagar"],
  },
  categories: [
    {
      title: "Men",
      image: "men.webp",
      items: [
        { name: "Shirt", price: 60 },
        { name: "Pant", price: 80 },
        { name: "Suit", price: 300 },
      ],
    },
    // Add other categories similarly
  ],
};
