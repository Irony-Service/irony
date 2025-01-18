"use client";

import * as React from "react";
import ServiceBlock from "./ServiceBlock";
import { OrderDetailsProps, OrderItem } from "./types";
import Image from "next/image";
import Link from "next/link";
import { useState } from "react";

export default function OrderDetails(props: OrderDetailsProps) {
  console.log("OrderDetails", props);
  const order = props.order;
  const { location_service_prices } = props;
  // console.log(order);
  const orderId = order?.simple_id || order?.order_id;
  const customerName = order.user_id;
  const phoneNumber = order.user_wa_id;
  const countRange = order.count_range_description + " clothes";

  const emptyOrderItem = {
    service: "",
    dress: "",
    count: "",
  };

  const [orderItems, setOrderItems] = useState<OrderItem[]>([emptyOrderItem]);

  const addNewOrderItem = () => {
    setOrderItems([...orderItems, emptyOrderItem]);
  };

  const handleInputChange = (index: number, field: keyof OrderItem, value: string) => {
    const updatedOrderItems = [...orderItems];
    updatedOrderItems[index][field] = value;
    setOrderItems(updatedOrderItems);
  };

  const removeOrderItem = (indexToRemove: number) => {
    setOrderItems((currentOrderItems) => currentOrderItems.filter((_, index) => index !== indexToRemove));
  };

  return (
    <div className="flex flex-col justify-between px-2.5 py-3 w-full h-full bg-white">
      <div className="flex flex-col w-full">
        <div className="flex flex-col w-full">
          <div className="flex flex-col w-full">
            <div className="flex justify-between items-center w-full">
              <div className="self-stretch my-auto text-sm font-medium text-gray-700">Order : {orderId}</div>
              <div className="flex justify-end gap-2.5 items-center">
                <div className="p-[6px] bg-amber-300 rounded-full">
                  <Link href={`tel:+${phoneNumber}`}>
                    <Image width={16} height={16} loading="lazy" src="/vector_phone.svg" alt="" className="" />
                  </Link>
                </div>
                <div className="p-[6px] bg-amber-300 rounded-full">
                  <Link href={order.maps_link || ""}>
                    <Image width={16} height={16} loading="lazy" src="/maps_arrow.svg" alt="" className="" />
                  </Link>
                </div>
                <button onClick={props.onClose} className="p-[6px] bg-amber-300 rounded-full">
                  <Image width={16} height={16} loading="lazy" src="/vector_close.svg" alt="" className="" />
                </button>
              </div>
            </div>
            <div className="mt-4 text-sm font-medium text-gray-700">Name: {customerName}</div>
            <div className="mt-4 text-sm font-medium text-gray-700">
              Number:{" "}
              <Link href={`tel:+${phoneNumber}`} className="underline">
                {phoneNumber}
              </Link>
            </div>
            <div className="mt-4 text-sm font-medium text-gray-700">Count range : {countRange}</div>
            <div className="mt-4 text-sm font-medium text-gray-700">Services :</div>
          </div>
          <div className="flex flex-col gap-2.5 justify-center mt-2 w-full">
            {orderItems.map((service, index) => (
              <ServiceBlock
                key={`service-block-${index}`} // Changed key to be more specific
                index={index}
                onClose={removeOrderItem}
                onInputChange={handleInputChange}
                location_service_prices={location_service_prices}
                {...service}
              />
            ))}
            <div className="flex justify-center items-center self-center p-[8px] bg-amber-300 rounded-full">
              <button onClick={addNewOrderItem}>
                <Image width={16} height={16} loading="lazy" src="/vector_plus.svg" alt="" />
              </button>
            </div>
          </div>
        </div>
      </div>
      <div className="sticky bottom-0 flex flex-col mt-4 w-full font-medium text-center">
        <button className="gap-2.5 self-start text-sm text-amber-200">Issue? click here.</button>
        <button className="gap-2.5 self-stretch p-2.5 mt-1.5 w-full text-base text-gray-700 whitespace-nowrap bg-amber-300 rounded-full">Confirm</button>
      </div>
    </div>
  );
}
