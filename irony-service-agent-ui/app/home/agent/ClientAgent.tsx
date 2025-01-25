"use client";
import Image from "next/image";
import Row from "./Row";
import { useSwipeable } from "react-swipeable";
import { useEffect, useState } from "react";
import { format, parse } from "date-fns";
import Util from "../util/util";
import OrderDetailsAgent from "./order/OrderDetailsAgent"; // Update import
import { Service, ServicePrices } from "../delivery/order/types";

interface HomeProps {
  responses: {
    orders: any;
    service_location_prices: any;
  };
}

type TimeSlotItem = {
  slot: string;
  orders: any[];
};

type DateItem = {
  date: string;
  time_slots: TimeSlotItem[];
};

type Section = {
  key: string;
  label: string;
  dates: DateItem[];
};

type ServiceLocationPrices = {
  [key: string]: ServicePrices[];
};

export default function HomeClient(props: HomeProps) {
  const { orders: orders_response, service_location_prices: service_location_prices_response } = props.responses;
  console.log(orders_response, service_location_prices_response);
  const data = orders_response;
  const sections: Section[] = orders_response.data;
  const service_locations_prices: ServiceLocationPrices = service_location_prices_response.data;

  const [currentIndex, setCurrentIndex] = useState(0);
  const [error, setError] = useState(data.success ? null : data.error);
  const [showOrder, setShowOrder] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [selectedServiceLocationPrices, setSelectedServiceLocationPrices] = useState<ServicePrices[]>([]);

  // Handlers for swiping
  const handlers = useSwipeable({
    onSwipedLeft: () => handleSwipe(1), // Next section
    onSwipedRight: () => handleSwipe(-1), // Previous section
    trackMouse: true, // Allows swipe gestures with a mouse
  });

  const handleSwipe = (direction: number) => {
    setCurrentIndex((prev) => {
      const newIndex = prev + direction;
      if (newIndex < 0) return 0; // Prevent swiping before the first section
      if (newIndex >= sections.length) return sections.length - 1; // Prevent swiping after the last section
      return newIndex;
    });
  };

  const handleShowOrder = (order: any) => {
    setSelectedOrder(order);
    setSelectedServiceLocationPrices(service_locations_prices[order?.service_location_id] || []); // Set your service location prices here if needed
    setShowOrder(true);
  };

  const handleCloseOrder = () => {
    setShowOrder(false);
    setSelectedOrder(null);
    setSelectedServiceLocationPrices([]);
  };

  const [priceServiceMap, setPriceServiceMap] = useState<Map<string, string>>(new Map());
  const [priceNameMap, setPriceNameMap] = useState<Map<string, string>>(new Map());
  useEffect(() => {
    const newServiceMap = new Map<string, string>();
    Object.values(service_locations_prices).forEach((servicePrices) => {
      servicePrices.forEach((price) => {
        if (price.prices && price.service) {
          price.prices.forEach((p) => {
            priceNameMap.set(p._id, p.category);
            newServiceMap.set(p._id, price.service.service_name);
          });
        }
      });
    });
    setPriceNameMap(priceNameMap);
    setPriceServiceMap(newServiceMap);
  }, [priceNameMap, service_locations_prices]);

  return (
    <div className="">
      <div {...handlers} className="relative flex overflow-hidden overflow-y-scroll w-full min-h-screen">
        {sections.map((section, index) => (
          <div
            key={index}
            className={`absolute w-full flex flex-col justify-center transition-transform duration-300 ${
              currentIndex === index ? "translate-x-0" : currentIndex < index ? "translate-x-full" : "-translate-x-full"
            }`}
          >
            <div className="flex w-full justify-between content-center py-3 my-2">
              <button onClick={() => handleSwipe(-1)}>
                <Image className="object-contain text-gray-700" src="/mingcute_left-line_black.svg" alt="Previous" width={28} height={28} />
              </button>
              <h1 className="text-3xl font-bold text-amber-300">{section.label}</h1>
              <button onClick={() => handleSwipe(1)}>
                <Image className="object-contain text-gray-700" src="/mingcute_right-line_black.svg" alt="Next" width={28} height={28} />
              </button>
            </div>
            {section.dates.map((dateItem, index) => (
              <section key={index} className={`w-full bg-gray-100 ${index != section.dates.length - 1 ? "py-4 border-b" : ""}`}>
                <div className="w-[96%]  mx-auto">
                  <h1 className="text-2xl  text-gray-700 font-semibold mb-5 px-2">
                    {Util.formatDate(dateItem.date)} ({Util.getOrdersInDate(dateItem.time_slots)} Orders)
                  </h1>

                  {dateItem.time_slots.map((timeSlotItem, index) => (
                    <div key={index} className="flex flex-col text-gray-700 rounded-3xl overflow-hidden mb-6 border">
                      <div className="flex justify-between items-center h-10 px-4 bg-amber-300">
                        <h2 className="text-base">
                          Slot : {timeSlotItem?.orders[0]?.time_slot_description} ({timeSlotItem.orders.length} Orders)
                        </h2>
                      </div>
                      <div className="text-xs">
                        {timeSlotItem.orders.map((order, index) => (
                          <Row
                            key={index}
                            services={order?.services?.map((service: any) => service?.service_name)}
                            order={order} // Add this line
                            lastRow={index == timeSlotItem.orders.length - 1}
                            onShowOrder={handleShowOrder} // Add this line
                          />
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            ))}
          </div>
        ))}
        {showOrder && (
          <div className="w-full min-h-screen z-50 overflow-y-auto">
            <OrderDetailsAgent order={selectedOrder} priceServiceMap={priceServiceMap} priceNameMap={priceNameMap} onClose={handleCloseOrder} />
          </div>
        )}
      </div>
      {error && <p className="text-red-500">{error}</p>}
    </div>
  );
}
