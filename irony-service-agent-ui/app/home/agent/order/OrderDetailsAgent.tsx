"use client";

import * as React from "react";
import { useState, useRef, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import apiClient from "@/utils/axiosClient";
import SlidingButton from "../../components/SlidingButton";

interface OrderItem {
  price_id: string;
  count: number;
  amount: number;
}

export interface OrderDetailsProps {
  order: any;
  priceServiceMap: Map<string, string>;
  priceNameMap: Map<string, string>;
  onClose: () => void;
}

export default function OrderDetailsAgent(props: OrderDetailsProps) {
  const order = props.order;
  const orderItems: OrderItem[] = order.order_items || [];
  const orderId = order?.simple_id || order?.order_id;
  const customerName = order.user_id;
  const phoneNumber = order.user_wa_id;
  const countRange = order.count_range_description + " clothes";
  const notes = order.notes || "";

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleConfirm = async () => {
    try {
      setIsSubmitting(true);
      setMessage(null);

      const newOrder = {
        order_id: orderId,
        current_status: order.status,
        new_status: "IN_PROGRESS",
      };

      const response = await apiClient.post<{ success: boolean; message: string }>("/updateOrder", newOrder);

      setMessage({
        type: "success",
        text: response.message || "Order confirmed successfully!",
      });

      // Close the order details after 2 seconds on success
      setTimeout(() => {
        props.onClose();
      }, 2000);
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
      <div className="flex flex-col w-full space-y-4">
        {/* Header */}
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

        {/* Customer Details */}
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

        {/* Services List - Read Only */}
        <div>
          <div className="text-lg font-semibold text-gray-700 mb-4">Services</div>
          <div className="space-y-3">
            {orderItems.map((item, index) => (
              <div key={index} className="bg-gray-50 p-4 rounded-lg">
                <div className="grid grid-cols-4 gap-2">
                  <div>
                    <span className="text-gray-500 text-sm">Service:</span>
                    <p className="font-medium">{props.priceServiceMap.get(item.price_id)}</p>
                  </div>
                  <div>
                    <span className="text-gray-500 text-sm">Category:</span>
                    <p className="font-medium">{props.priceNameMap.get(item.price_id)}</p>
                  </div>
                  <div>
                    <span className="text-gray-500 text-sm">Count:</span>
                    <p className="font-medium">{item.count}</p>
                  </div>
                  <div>
                    <span className="text-gray-500 text-sm">Price:</span>
                    <p className="font-medium">₹{item.amount}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Bill Details */}
        {/* <div className="mt-6">
          <div className="text-sm font-medium text-gray-700 mb-2">Bill Details:</div>
          <div className="border rounded-lg p-4 bg-gray-50">
            <div className="space-y-3">
              {orderItems.map((item, index) => (
                <div key={index} className="flex justify-between text-sm">
                  <div>
                    <p className="font-medium">{item.service.service.service_name}</p>
                    <p className="text-gray-500">
                      {item.count} items • ₹{item.amount / item.count} each
                    </p>
                  </div>
                  <p className="font-medium">₹{item.amount}</p>
                </div>
              ))}
              <div className="border-t pt-3 mt-3 flex justify-between font-medium">
                <span>Total Amount</span>
                <span>₹{orderItems.reduce((sum, item) => sum + item.amount, 0)}</span>
              </div>
            </div>
          </div>
        </div> */}

        {/* Notes Section - Read Only */}
        {notes && (
          <div className="mt-6">
            <div className="text-sm font-medium text-gray-700 mb-2">Notes:</div>
            <div className="p-3 bg-gray-50 rounded-lg text-sm text-gray-700">{notes}</div>
          </div>
        )}
      </div>

      <div className="sticky bottom-0 flex flex-col mt-4 w-full font-medium text-center bg-white p-4 border-t">
        {message && <div className={`mb-4 p-3 rounded-lg text-sm ${message.type === "success" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>{message.text}</div>}

        <SlidingButton onComplete={handleConfirm} isLoading={isSubmitting} />
      </div>
    </div>
  );
}
