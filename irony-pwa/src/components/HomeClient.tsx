"use client";

import dynamic from "next/dynamic";

const CartButton = dynamic(() => import("./CartButton"), {
  ssr: false,
  loading: () => <div>Loading...</div>,
});

const Categories = dynamic(() => import("./Categories"), {
  ssr: false,
  loading: () => <div>Loading...</div>,
});

const Hero = dynamic(() => import("./Hero"), {
  ssr: false,
  loading: () => <div>Loading...</div>,
});

const Navbar = dynamic(() => import("./Navbar"), {
  ssr: false,
  loading: () => <div>Loading...</div>,
});

const Services = dynamic(() => import("./Services"), {
  ssr: false,
  loading: () => <div>Loading...</div>,
});

export default function HomeClient() {
  return (
    <>
      <Navbar />
      <Hero />
      <Services />
      <Categories />
      <CartButton />
    </>
  );
}
