"use client";

import * as React from "react";
import ServiceBlock from "./ServiceBlock";
import { OrderDetailsProps, OrderItemInput, NewOrder } from "./types";
import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import apiClient from "@/utils/axiosClient";

export default function OrderDetails(props: OrderDetailsProps) {
  console.log("OrderDetails", props);
  const order = props.order;
  const { location_service_prices } = props;
  // console.log(order);
  const orderId = order?._id;
  const customerName = order.user_id;
  const phoneNumber = order.user_wa_id;
  const countRange = order.count_range_description + " clothes";
  const totalPrice = 0;

  const emptyOrderItem = {
    service: 0,
    dress: 0,
    count: 0,
  };

  const [orderItems, setOrderItems] = useState<OrderItemInput[]>([emptyOrderItem]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [notes, setNotes] = useState("");

  const addNewOrderItem = () => {
    setOrderItems([...orderItems, emptyOrderItem]);
  };

  const handleInputChange = (index: number, field: keyof OrderItemInput, value: string) => {
    const updatedOrderItems = [...orderItems];
    updatedOrderItems[index][field] = Number(value);
    setOrderItems(updatedOrderItems);
  };

  const removeOrderItem = (indexToRemove: number) => {
    setOrderItems((currentOrderItems) => currentOrderItems.filter((_, index) => index !== indexToRemove));
  };

  const handleConfirm = async () => {
    try {
      setIsSubmitting(true);
      setMessage(null);

      const newOrder: NewOrder = {
        order_id: orderId,
        current_status: order.order_status[0].status,
        new_status: "WORK_IN_PROGRESS",
        items: orderItems.map((item) => ({
          price_id: location_service_prices[item.service].prices[item.dress].id,
          count: item.count,
          amount: item.count * location_service_prices[item.service].prices[item.dress].price,
        })),
        total_price: orderItems.reduce((sum, item) => sum + item.count * location_service_prices[item.service].prices[item.dress].price, 0),
        notes: notes.trim(), // Add notes to the request
      };

      const response = await apiClient.post<{ success: boolean; message: string; body: any }>("/updateOrder", newOrder);

      console.log(response);
      if (!response.success) {
        throw new Error(response.message || "Failed to confirm order");
      }

      const subIdMessage = Object.entries(response.body?.sub_id_dict)
        .map(([key, value]) => `${key} : ${value}`)
        .join("\n");

      setMessage({
        type: "success",
        text: `${response.message}\n Order No's : \n${subIdMessage}` || "Order confirmed successfully!",
      });

      // // Close the order details after 2 seconds on success
      // setTimeout(() => {
      //   props.onClose();
      // }, 2000);
    } catch (error: any) {
      setMessage({
        type: "error",
        text: error.message || "Failed to confirm order",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col justify-between px-2.5 py-3 w-full h-full bg-white relative">
      <div className="flex flex-col w-full">
        <div className="flex flex-col w-full space-y-4">
          {/* Header with Order ID and Action Buttons */}
          <div className="flex justify-between items-center w-full bg-gray-50 p-3 rounded-lg">
            <div className="text-sm font-semibold text-gray-700">Order #{orderId}</div>
            <div className="flex gap-2">
              <Link href={`tel:+${phoneNumber}`} className="p-2 bg-amber-300 rounded-full hover:bg-amber-400 transition-colors">
                <Image width={16} height={16} loading="lazy" src="/vector_phone.svg" alt="Call" />
              </Link>
              <Link href={order.maps_link || ""} className="p-2 bg-amber-300 rounded-full hover:bg-amber-400 transition-colors">
                <Image width={16} height={16} loading="lazy" src="/maps_arrow.svg" alt="Maps" />
              </Link>
              <button onClick={props.onClose} className="p-2 bg-amber-300 rounded-full hover:bg-amber-400 transition-colors">
                <Image width={16} height={16} loading="lazy" src="/vector_close.svg" alt="Close" />
              </button>
            </div>
          </div>

          {/* Customer Details Card */}
          <div className="bg-gray-50 p-4 rounded-lg space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-gray-500">Customer Name:</span>
              <span className="font-medium">{customerName}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-500">Phone:</span>
              <Link href={`tel:+${phoneNumber}`} className="font-medium text-amber-600 hover:text-amber-700">
                {phoneNumber}
              </Link>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-500">Count Range:</span>
              <span className="font-medium">{countRange}</span>
            </div>
          </div>

          {/* Services Header */}
          <div className="text-lg font-semibold text-gray-700">Services</div>
        </div>

        <div className="flex flex-col gap-2.5 justify-center mt-2 w-full">
          {orderItems.map((service, index) => (
            <ServiceBlock
              key={`service-block-${index}`} // Changed key to be more specific
              index={index}
              onClose={removeOrderItem}
              onInputChange={handleInputChange}
              location_service_prices={location_service_prices}
              service={service.service.toString()}
              dress={service.dress.toString()}
              count={service.count.toString()}
            />
          ))}
          <div className="flex justify-center items-center self-center p-[8px] bg-amber-300 rounded-full">
            <button onClick={addNewOrderItem}>
              <Image width={16} height={16} loading="lazy" src="/vector_plus.svg" alt="" />
            </button>
          </div>
        </div>
        <div className="flex flex-col">
          <div className="mt-4"></div>
          <div className="text-sm font-medium text-gray-700 mb-2">Bill Details:</div>
          <div className="border rounded p-3">
            {orderItems.map((item, index) => {
              const service = location_service_prices[item.service].service;
              const dress_type_obj = location_service_prices[item.service].prices[item.dress];
              if (!isNaN(item.count) && item.count > 0) {
                return (
                  <div key={`bill-item-${index}`} className="flex justify-between mb-2">
                    <div className="flex flex-col text-sm">
                      <span className="font-medium">
                        {service.service_name} • {dress_type_obj.category}
                      </span>
                      <span className="text-gray-500">
                        {item.count} items • ₹{dress_type_obj.price} each
                      </span>
                    </div>
                    <div className="text-sm font-medium">₹{(item.count * dress_type_obj.price).toFixed(2)}</div>
                  </div>
                );
              }
            })}
            <div className="border-t mt-2 pt-2 flex justify-between">
              <div className="text-sm font-medium">Total</div>
              <div className="text-sm font-medium">₹{orderItems.reduce((sum, item) => sum + Number(item.count) * location_service_prices[item.service].prices[item.dress]?.price, 0).toFixed(2)}</div>
            </div>
          </div>

          {/* Notes Section */}
          <div className="mt-6">
            <div className="text-sm font-medium text-gray-700 mb-2">Notes (Optional):</div>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add any special instructions or notes here..."
              className="w-full h-24 p-3 border rounded-lg bg-gray-50 text-sm focus:outline-none focus:border-amber-300 resize-none"
            />
          </div>
        </div>
      </div>
      <div className="sticky bottom-0 flex flex-col mt-4 w-full font-medium text-center bg-white p-4 border-t">
        {message && <div className={`mb-4 p-3 rounded-lg text-sm ${message.type === "success" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>{message.text}</div>}
        <button className="gap-2.5 self-start text-sm text-amber-200">Issue? click here.</button>
        <button
          onClick={handleConfirm}
          disabled={isSubmitting || orderItems.length === 0}
          className={`gap-2.5 self-stretch p-2.5 mt-1.5 w-full text-base text-gray-700 whitespace-nowrap rounded-full transition-colors ${
            isSubmitting || orderItems.length === 0 ? "bg-gray-300 cursor-not-allowed" : "bg-amber-300 hover:bg-amber-400"
          }`}
        >
          {isSubmitting ? "Confirming..." : "Confirm"}
        </button>
      </div>
    </div>
  );
}
