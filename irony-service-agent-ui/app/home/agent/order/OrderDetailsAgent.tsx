"use client";

import apiClient from "@/utils/axiosClient";
import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import OrderServicesList from "../../components/OrderServicesList";
import SlidingButton from "../../components/SlidingButton";
import { OrderItem } from "../../types/types";

export interface OrderDetailsProps {
  order: any;
  priceServiceMap: Map<string, string>;
  priceNameMap: Map<string, string>;
  onClose: () => void;
}

export default function OrderDetailsAgent(props: OrderDetailsProps) {
  const order = props.order;
  const orderItems: OrderItem[] = order.order_items || [];
  const orderId = order?._id;
  let simpleId = order?.simple_id || orderId;
  const customerName = order.user_id;
  const phoneNumber = order.user_wa_id;
  const countRange = order.count_range_description + " clothes";
  const notes = order.notes || "";
  const showAction = order.order_status[0]?.status === "WORK_IN_PROGRESS";

  if (order?.sub_id) {
    simpleId += `-${order.sub_id}`;
  }

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleConfirm = async () => {
    try {
      setIsSubmitting(true);
      setMessage(null);

      const newOrder = {
        order_id: orderId,
        current_status: order?.order_status[0]?.status,
        new_status: "DELIVERY_PENDING",
      };

      const response = await apiClient.put<{ success: boolean; message: string }>("/agent/orders", newOrder);

      if (!response.success) {
        throw new Error(response.message || "Failed to confirm order");
      }

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
      return Promise.reject(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col justify-between px-2.5 py-3 w-full h-full bg-white relative">
      <div className="flex flex-col w-full space-y-4">
        {/* Header */}
        <div className="flex justify-between items-center w-full bg-gray-50 p-3 rounded-lg">
          <div className="text-sm font-semibold text-gray-700">Order #{simpleId}</div>
          <div className="flex gap-2">
            <Link href={`tel:+${phoneNumber}`} className="p-2 bg-amber-300 rounded-full hover:bg-amber-400 transition-colors">
              <Image width={16} height={16} loading="lazy" src="/service/vector_phone.svg" alt="Call" />
            </Link>
            <Link href={order.maps_link || ""} className="p-2 bg-amber-300 rounded-full hover:bg-amber-400 transition-colors">
              <Image width={16} height={16} loading="lazy" src="/service/maps_arrow.svg" alt="Maps" />
            </Link>
            <button onClick={props.onClose} className="p-2 bg-amber-300 rounded-full hover:bg-amber-400 transition-colors">
              <Image width={16} height={16} loading="lazy" src="/service/vector_close.svg" alt="Close" />
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
        <OrderServicesList orderItems={orderItems} priceServiceMap={props.priceServiceMap} priceNameMap={props.priceNameMap}></OrderServicesList>

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

        {showAction && <SlidingButton onComplete={handleConfirm} isLoading={isSubmitting} />}
      </div>
    </div>
  );
}
