"use client";
import Image from "next/image";
import Row from "./Row";
import { useSwipeable } from "react-swipeable";
import { useState } from "react";
import { format, parse } from "date-fns";
interface HomeProps {
  data: any;
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

// const sections: Section[] = [
//   { title: "Section 1", data: "Data for section 1" },
//   { title: "Section 2", data: "Data for section 2" },
//   { title: "Section 3", data: "Data for section 3" },
//   { title: "Section 34=", data: "Data for section 3" },
//   { title: "Section 34=", data: "Data for section 3" },
//   { title: "Section 34=", data: "Data for section 3" },
// ];
export default function HomeClient({ data }: HomeProps) {
  const sections: Section[] = data.body;

  const [currentIndex, setCurrentIndex] = useState(0);
  const [error, setError] = useState(data.success ? null : data.error);

  // Handlers for swiping
  const handlers = useSwipeable({
    onSwipedLeft: () => handleSwipe(1), // Next section
    onSwipedRight: () => handleSwipe(-1), // Previous section
    preventDefaultTouchmoveEvent: true,
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

  function getOrdersInDate(time_slots: TimeSlotItem[]): import("react").ReactNode {
    return time_slots.reduce((totalOrders, timeSlot) => totalOrders + timeSlot.orders.length, 0);
  }

  const formatDate = (inputDate: string): string => {
    const date = parse(inputDate, "dd-MM-yyyy", new Date());
    return format(date, "eee, d MMM");
  };

  return (
    <div className="mx-auto w-full max-w-[480px]">
      <div {...handlers} className="relative flex overflow-hidden overflow-y-auto w-full min-h-screen">
        {sections.map((section, index) => (
          <div
            key={index}
            className={`absolute w-full flex flex-col justify-center transition-transform duration-300 ${
              currentIndex === index ? "translate-x-0" : currentIndex < index ? "translate-x-full" : "-translate-x-full"
            }`}
          >
            <div className="flex w-full justify-between content-center py-3 my-2">
              <button onClick={() => handleSwipe(-1)}>
                <Image className="object-contain text-amber-200" src="/mingcute_left-line.svg" alt="Previous" width={28} height={28} />
              </button>
              <h1 className="text-3xl font-bold text-sky-300">{section.label}</h1>
              <button onClick={() => handleSwipe(1)}>
                <Image className="object-contain text-amber-200" src="/mingcute_right-line.svg" alt="Next" width={28} height={28} />
              </button>
            </div>
            {section.dates.map((dateItem, index) => (
              <section key={index} className="w-full bg-gray-100 py-4 border-b">
                <div className="w-[96%]  mx-auto">
                  <h1 className="text-2xl  text-sky-300 font-semibold mb-5 px-2">
                    {formatDate(dateItem.date)} ({getOrdersInDate(dateItem.time_slots)} Orders)
                  </h1>

                  {dateItem.time_slots.map((timeSlotItem, index) => (
                    <div key={index} className="flex flex-col text-gray-700 rounded-3xl overflow-hidden mb-10">
                      <div className="flex justify-between items-center h-10 px-4 bg-amber-300">
                        <h2 className="text-base">
                          Slot : {timeSlotItem?.orders[0]?.time_slot_description} ({timeSlotItem.orders.length} Orders)
                        </h2>
                      </div>
                      <div className="text-xs">
                        {timeSlotItem.orders.map((order, index) => (
                          <Row
                            key={index}
                            data={{ count_range: order?.count_range_description, services: order?.services?.map((service: any) => service?.service_name), distance: order?.distance || "N/a" }}
                            lastRow={index == timeSlotItem.orders.length - 1 ? true : false}
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
      </div>
      {error && <p className="text-red-500">{error}</p>}
    </div>
  );
}
