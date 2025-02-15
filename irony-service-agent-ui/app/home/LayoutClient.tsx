"use client";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useState } from "react";
import CreateOrderDialog from "./components/CreateOrderDialog";
import apiClient from "@/utils/axiosClient";

const links = [
  { name: "Home Agent", href: "/home/agent" },
  {
    name: "Home Delivery",
    href: "/home/delivery",
  },
];

export default function LayoutClient() {
  const pathname = usePathname();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [locationServicePrices, setLocationServicePrices] = useState(null);

  const handleOpenDialog = async () => {
    try {
      // Fetch location service prices if not already loaded
      if (!locationServicePrices) {
        const response: any = await apiClient.get("/servicePricesForServiceLocations");
        if (!response.data) {
          throw new Error("Failed to fetch base location service prices");
        }
        setLocationServicePrices(response.data);
      }
      setIsDialogOpen(true);
    } catch (error) {
      console.error("Failed to fetch location service prices:", error);
    }
  };

  return (
    <>
      <div className="sticky bottom-0 left-0 w-full h-12 flex mt-2">
        <div className={`w-[40%] h-full rounded-tl-2xl shadow-2xl shadow-gray-900  ${pathname === links[0].href ? "bg-gray-800" : "bg-white"}`}>
          <a key={links[0].name} href={links[0].href} className="h-full flex justify-center content-center">
            <Image src={`${pathname === links[0].href ? "/material-symbols_iron-outline-rounded.svg" : "/material-symbols_iron-outline-rounded_black.svg"}`} alt="Previous" width={28} height={28} />
          </a>
        </div>
        <div className="w-[20%] h-full flex justify-center items-center bg-amber-300 shadow-2xl shadow-gray-900">
          <button onClick={handleOpenDialog} className="p-2 rounded-full hover:bg-amber-400 transition-colors">
            <Image src="/vector_plus.svg" alt="Create Order" width={24} height={24} />
          </button>
        </div>
        <div className={`w-[40%] h-full rounded-tr-2xl shadow-2xl shadow-gray-900 ${pathname === links[1].href ? "bg-gray-800" : "bg-white"}`}>
          <a key={links[1].name} href={links[1].href} className="h-full flex justify-center content-center">
            <Image src={`${pathname === links[1].href ? "/ic_outline-delivery-dining.svg" : "/ic_outline-delivery-dining_black.svg"}`} alt="Previous" width={28} height={28} />
          </a>
        </div>
      </div>

      {/* Dialog */}
      {locationServicePrices && <CreateOrderDialog isOpen={isDialogOpen} onClose={() => setIsDialogOpen(false)} service_locations_prices={locationServicePrices} />}
    </>
  );
}
