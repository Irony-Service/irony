"use client";

import * as React from "react";
import { useState, useEffect } from "react";
import { Price, ServiceBlockProps, ServicePrices } from "./types";
import Image from "next/image";

export default function ServiceBlock(props: ServiceBlockProps) {
  const { location_service_prices } = props;
  const [dressOptions, setDressOptions] = useState<Price[]>([]);

  const updateDressOptions = (serviceId: string) => {
    const selectedServicePrice = location_service_prices.find((sp: ServicePrices) => sp.service.id === serviceId);
    if (selectedServicePrice && selectedServicePrice.prices) {
      setDressOptions(selectedServicePrice.prices);
    } else {
      setDressOptions([]);
    }
  };

  const handleServiceChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const serviceId = e.target.value;
    updateDressOptions(serviceId);
    props.onInputChange(props.index, "service", serviceId);
  };

  const handleClose = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    props.onClose(props.index);
  };

  useEffect(() => {
    // Set initial service and dress options if service_prices is not empty
    if (location_service_prices.length > 0) {
      const initialServiceId = location_service_prices[0].service.id;

      const selectedServicePrice = location_service_prices.find((sp: ServicePrices) => sp.service.id === initialServiceId);
      if (selectedServicePrice && selectedServicePrice.prices) {
        setDressOptions(selectedServicePrice.prices);
      } else {
        setDressOptions([]);
      }
    }
  }, [location_service_prices]);

  return (
    <div className="relative flex overflow-hidden flex-col p-2 w-full text-xs font-medium text-gray-700 bg-amber-300 rounded-xl">
      <button onClick={handleClose} className="absolute top-1 right-2 p-1 rounded-full bg-white hover:bg-gray-100">
        <Image src="/vector_close.svg" alt="Close" width={8} height={8} />
      </button>
      <div className="flex overflow-hidden justify-between items-center w-full mt-5">
        <div className="flex-1 shrink self-stretch my-auto basis-0 max-w-[60px]">Service</div>
        <div className="flex flex-1 shrink self-stretch my-auto h-6 bg-white rounded-xl basis-0 min-w-[240px] w-[244px]">
          <select className="w-full h-full px-2 bg-transparent border-none outline-none" value={props.service} onChange={handleServiceChange}>
            {location_service_prices.map((service_price: ServicePrices) => (
              <option key={service_price.service.id} value={service_price.service.id}>
                {service_price.service.service_name}
              </option>
            ))}
          </select>
        </div>
      </div>
      <div className="flex overflow-hidden justify-between items-center mt-2.5 w-full whitespace-nowrap">
        <div className="flex-1 shrink self-stretch my-auto basis-0 max-w-[60px]">Dress</div>
        <div className="flex flex-1 shrink self-stretch my-auto h-6 bg-white rounded-xl basis-0 min-w-[240px] w-[244px]">
          <select className="w-full h-full px-2 bg-transparent border-none outline-none" value={props.dress} onChange={(e) => props.onInputChange(props.index, "dress", e.target.value)}>
            {dressOptions.map((dress) => (
              <option key={dress.id} value={dress.id}>
                {dress.category} (₹{dress.price})
              </option>
            ))}
          </select>
        </div>
      </div>
      <div className="flex overflow-hidden justify-between items-center mt-2.5 w-full">
        <div className="flex-1 shrink self-stretch my-auto basis-0 max-w-[60px]">Count </div>
        <div className="flex flex-1 shrink self-stretch my-auto h-6 bg-white rounded-xl basis-0 min-w-[240px] w-[244px]">
          <input
            type="number"
            min={1}
            value={props.count}
            onChange={(e) => props.onInputChange(props.index, "count", e.target.value)}
            className="w-full h-full px-2 text-center bg-transparent border-none outline-none"
          />
        </div>
      </div>
    </div>
  );
}
