"use client";

import apiClient from "@/utils/axiosClient";
import Image from "next/image";
import { useState } from "react";
import { OrderItemInput } from "../types/types";
import AddOrderServices from "./AddOrderServices";
import BillDetails from "./BillDetails";

interface CreateOrderDialogProps {
  isOpen: boolean;
  onClose: () => void;
  service_locations_prices: any;
}

export default function CreateOrderDialog({ isOpen, onClose, service_locations_prices }: CreateOrderDialogProps) {
  const [orderItems, setOrderItems] = useState<OrderItemInput[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const service_location_id: any = Object.keys(service_locations_prices)[0];
  const location_service_prices: any = Object.values(service_locations_prices)[0];

  const [formData, setFormData] = useState({
    customerName: "",
    phoneNumber: "",
    // locationNickname: "",
    notes: "",
  });

  if (!isOpen) return null;

  const handleOrderItemsChange = (items: OrderItemInput[]) => {
    setOrderItems(items);
  };

  const handleSubmit = async () => {
    try {
      setIsSubmitting(true);
      setMessage(null);

      const newOrder = {
        user_id: formData.customerName,
        user_wa_id: formData.phoneNumber,
        service_location_id: service_location_id,
        // location_nickname: formData.locationNickname,
        notes: formData.notes,
        items: orderItems.map((item) => ({
          price_id: location_service_prices[item.service].prices[item.dress]._id,
          count: item.count,
          amount: item.count * location_service_prices[item.service].prices[item.dress].price,
        })),
        total_price: orderItems.reduce((sum, item) => sum + item.count * location_service_prices[item.service].prices[item.dress].price, 0),
      };

      const response: any = await apiClient.post("/createOrder", newOrder);

      if (!response.success) {
        throw new Error(response.message || "Failed to create order");
      }

      setMessage({
        type: "success",
        text: "Order created successfully!",
      });

      setTimeout(() => {
        onClose();
      }, 2000);
    } catch (error: any) {
      setMessage({
        type: "error",
        text: error.message || "Failed to create order",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-center items-center">
      <div className="bg-white rounded-lg w-full max-w-[480px] max-h-[90vh] overflow-y-auto m-4">
        <div className="flex flex-col p-4 gap-4">
          {/* Header */}
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">Create New Order</h2>
            <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full">
              <Image width={16} height={16} src="/service/vector_close.svg" alt="Close" />
            </button>
          </div>

          {/* Form Fields */}
          <div className="space-y-4">
            <input
              type="text"
              placeholder="Customer Name"
              value={formData.customerName}
              onChange={(e) => setFormData({ ...formData, customerName: e.target.value })}
              className="w-full p-3 border rounded-lg"
            />
            <input
              type="tel"
              placeholder="Phone Number"
              value={formData.phoneNumber}
              onChange={(e) => setFormData({ ...formData, phoneNumber: e.target.value })}
              className="w-full p-3 border rounded-lg"
            />
            {/* <input
              type="text"
              placeholder="Location Nickname"
              value={formData.locationNickname}
              onChange={(e) => setFormData({ ...formData, locationNickname: e.target.value })}
              className="w-full p-3 border rounded-lg"
            /> */}

            {/* Services */}
            <AddOrderServices location_service_prices={location_service_prices} onOrderItemsChange={handleOrderItemsChange} />

            {/* Bill Details */}
            <BillDetails orderItems={orderItems} location_service_prices={location_service_prices} />

            {/* Notes */}
            <textarea placeholder="Notes" value={formData.notes} onChange={(e) => setFormData({ ...formData, notes: e.target.value })} className="w-full p-3 border rounded-lg h-24 resize-none" />
          </div>

          {/* Message */}
          {message && <div className={`p-3 rounded-lg ${message.type === "success" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>{message.text}</div>}

          {/* Submit Button */}
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || orderItems.length === 0}
            className={`p-3 rounded-lg ${isSubmitting || orderItems.length === 0 ? "bg-gray-300" : "bg-amber-300 hover:bg-amber-400"}`}
          >
            {isSubmitting ? "Creating..." : "Create Order"}
          </button>
        </div>
      </div>
    </div>
  );
}
