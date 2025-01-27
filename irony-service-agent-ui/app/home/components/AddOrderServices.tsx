import { useState } from "react";
import Image from "next/image";
import ServiceBlock from "../delivery/order/ServiceBlock";
import { OrderItemInput } from "../types/types";

interface AddOrderServicesProps {
  location_service_prices: any;
  onOrderItemsChange: (items: OrderItemInput[]) => void;
}

export default function AddOrderServices({ location_service_prices, onOrderItemsChange }: AddOrderServicesProps) {
  const emptyOrderItem = {
    service: 0,
    dress: 0,
    count: 0,
  };

  const [orderItems, setOrderItems] = useState<OrderItemInput[]>([emptyOrderItem]);

  const addNewOrderItem = () => {
    const newItems = [...orderItems, emptyOrderItem];
    setOrderItems(newItems);
    onOrderItemsChange(newItems);
  };

  const handleInputChange = (index: number, field: keyof OrderItemInput, value: string) => {
    const updatedOrderItems = [...orderItems];
    updatedOrderItems[index][field] = Number(value);
    setOrderItems(updatedOrderItems);
    onOrderItemsChange(updatedOrderItems);
  };

  const removeOrderItem = (indexToRemove: number) => {
    const newItems = orderItems.filter((_, index) => index !== indexToRemove);
    setOrderItems(newItems);
    onOrderItemsChange(newItems);
  };

  return (
    <div className="flex flex-col gap-2.5 justify-center mt-2 w-full">
      {orderItems.map((service, index) => (
        <ServiceBlock
          key={`service-block-${index}`}
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
  );
}
