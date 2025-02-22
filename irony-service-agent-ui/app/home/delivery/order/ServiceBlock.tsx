"use client";

import * as React from "react";
import { useState, useEffect } from "react";
import { Price, ServiceBlockProps, ServicePrices } from "../../types/types";
import Image from "next/image";

export default function ServiceBlock(props: ServiceBlockProps) {
  const { location_service_prices } = props;
  const [dressOptions, setDressOptions] = useState<Price[]>([]);

  const updateDressOptions = (serviceId: string) => {
    const selectedServicePrice = location_service_prices.find((sp: ServicePrices) => sp.service._id === serviceId);
    if (selectedServicePrice && selectedServicePrice.prices) {
      setDressOptions(selectedServicePrice.prices);
    } else {
      setDressOptions([]);
    }
  };

  const handleServiceChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const serviceIndex = e.target.value;
    updateDressOptions(serviceIndex);
    props.onInputChange(props.index, "service", serviceIndex);
  };

  const handleClose = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    props.onClose(props.index);
  };

  useEffect(() => {
    // Set initial service and dress options if service_prices is not empty
    if (location_service_prices.length > 0) {
      const initialServiceId = location_service_prices[0].service._id;

      const selectedServicePrice = location_service_prices.find((sp: ServicePrices) => sp.service._id === initialServiceId);
      if (selectedServicePrice && selectedServicePrice.prices) {
        setDressOptions(selectedServicePrice.prices);
      } else {
        setDressOptions([]);
      }
    }
  }, [location_service_prices]);

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm w-full">
      <div className="flex items-center justify-between bg-amber-300 px-3 sm:px-4 py-2 rounded-t-lg">
        <h3 className="font-medium text-gray-700 text-sm sm:text-base">Service Item</h3>
        <button onClick={handleClose} className="p-1 sm:p-1.5 hover:bg-amber-400 rounded-full transition-colors">
          <Image src="/service/vector_close.svg" alt="Close" width={10} height={10} />
        </button>
      </div>

      <div className="p-3 sm:p-4 space-y-3 sm:space-y-4">
        {/* Service Selection */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
          <label className="text-sm font-medium text-gray-600 sm:w-20">Service</label>
          <select
            className="w-full h-9 px-2 sm:px-3 rounded-lg border border-gray-200 bg-gray-50 focus:outline-none focus:border-amber-300 text-sm"
            value={props.service}
            onChange={handleServiceChange}
          >
            {location_service_prices.map((service_price: ServicePrices, index: number) => (
              <option key={index} value={index}>
                {service_price.service.service_name}
              </option>
            ))}
          </select>
        </div>

        {/* Dress Selection */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
          <label className="text-sm font-medium text-gray-600 sm:w-20">Dress</label>
          <select
            className="w-full h-9 px-2 sm:px-3 rounded-lg border border-gray-200 bg-gray-50 focus:outline-none focus:border-amber-300 text-sm"
            value={props.dress}
            onChange={(e) => props.onInputChange(props.index, "dress", e.target.value)}
          >
            {dressOptions.map((dress, index: number) => (
              <option key={index} value={index}>
                {dress.category} (₹{dress.price})
              </option>
            ))}
          </select>
        </div>

        {/* Count Input */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
          <label className="text-sm font-medium text-gray-600 sm:w-20">Count</label>
          <input
            type="number"
            min={1}
            value={props.count}
            onChange={(e) => props.onInputChange(props.index, "count", e.target.value)}
            className="w-full h-9 px-2 sm:px-3 text-center rounded-lg border border-gray-200 bg-gray-50 focus:outline-none focus:border-amber-300 text-sm"
          />
        </div>
      </div>
    </div>
  );
}
