"use client";

import apiClient from "@/utils/axiosClient";
import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import { OrderItem, OrderItemWithValues, OrderStatus } from "../types/types";
import BillDetailsWithValues from "./BillDetailsWithValues";
import OrderServicesList from "./OrderServicesList";
import SlidingButton from "./SlidingButton";

export interface OrderDetailsProps {
  order: any;
  priceServiceMap: Map<string, string>;
  priceNameMap: Map<string, string>;
  actionStatusMap: Map<OrderStatus, OrderStatus>;
  showBillDetailsStatusList: OrderStatus[];
  onClose: (deleteOnClose: boolean) => void;
}

export default function OrderDetailsView(props: OrderDetailsProps) {
  const order = props.order;
  const orderItems: OrderItem[] = order.order_items || [];
  const orderId = order?._id;
  let simpleId = order?.simple_id || orderId;
  const customerName = order.user_id;
  const phoneNumber = order.user_wa_id;
  const countRange = (order.total_count ? order.total_count : order.count_range_description) + " clothes";
  const notes = order.notes || "";
  const currentOrderStatus = order.order_status[0]?.status;
  const showAction = props.actionStatusMap.has(currentOrderStatus);
  const showBillDetails = props.showBillDetailsStatusList.includes(currentOrderStatus);

  if (order?.sub_id) {
    simpleId += `-${order.sub_id}`;
  }

  const orderItemsBill: OrderItemWithValues[] = orderItems.map((item) => ({
    service_name: props.priceServiceMap.get(item.price_id) || "",
    dress_category: props.priceNameMap.get(item.price_id) || "",
    count: item.count,
    amount: item.amount,
  }));

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleConfirm = async () => {
    try {
      setIsSubmitting(true);
      setMessage(null);

      const newOrder = {
        order_id: orderId,
        current_status: currentOrderStatus,
        new_status: props.actionStatusMap.get(currentOrderStatus),
      };

      const response = await apiClient.post<{ success: boolean; message: string }>("/updateOrder", newOrder);

      if (!response.success) {
        throw new Error(response.message || "Failed to confirm order");
      }

      setMessage({
        type: "success",
        text: response.message || "Order updated successfully!",
      });

      // Close the order details after 2 seconds on success
      setTimeout(() => {
        props.onClose(true);
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
              <Image width={16} height={16} loading="lazy" src="/vector_phone.svg" alt="Call" />
            </Link>
            <Link href={order.maps_link || ""} className="p-2 bg-amber-300 rounded-full hover:bg-amber-400 transition-colors">
              <Image width={16} height={16} loading="lazy" src="/maps_arrow.svg" alt="Maps" />
            </Link>
            <button onClick={() => props.onClose(false)} className="p-2 bg-amber-300 rounded-full hover:bg-amber-400 transition-colors">
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
            <span className="text-gray-500">Count:</span>
            <span className="font-medium">{countRange}</span>
          </div>
        </div>

        {/* Services List - Read Only */}
        <OrderServicesList orderItems={orderItems} priceServiceMap={props.priceServiceMap} priceNameMap={props.priceNameMap}></OrderServicesList>

        {/* Bill Details */}
        {showBillDetails && <BillDetailsWithValues orderItems={orderItemsBill} />}

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
