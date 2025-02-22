export interface ServiceBlockProps {
  location_service_prices: ServicePrices[];
  service: string;
  dress: string;
  count: string;
  onClose: (index: number) => void;
  onInputChange: (index: number, key: keyof OrderItemInput, value: string) => void;
  index: number; // Add this line
}

export interface Service {
  _id: string;
  service_category: string;
  service_type: string;
  service_name: string;
  call_to_action_key: string;
}
export interface Price {
  _id: string;
  service_location_id: string;
  service_id: string;
  category_key: string;
  category: string;
  price: number;
  sort_order: number;
}
export interface ServicePrices {
  service: Service;
  prices: Price[];
}
export interface OrderDetailsProps {
  order: any;
  location_service_prices: ServicePrices[];
  priceServiceMap: Map<string, string>;
  priceNameMap: Map<string, string>;
  onClose: (deleteOnClose: boolean) => void;
}

export interface OrderItemInput {
  service: number;
  dress: number;
  count: number;
}

export interface NewOrder {
  order_id: string;
  current_status: string;
  new_status: string;
  location_nickname?: string;
  items: {
    price_id: string;
    count: number;
    amount: number;
  }[];
  notes: string;
  total_price: number;
}

export type ServiceLocationPrices = {
  [key: string]: ServicePrices[];
};

// Add these new shared types
export interface HomeProps {
  responses: {
    orders: any;
    service_location_prices: any;
  };
}

export type TimeSlotItem = {
  slot: string;
  orders: any[];
};

export type DateItem = {
  date: string;
  time_slots: TimeSlotItem[];
};

export type Section = {
  key: string;
  label: string;
  dates: DateItem[];
};

export enum OrderStatus {
  SERVICE_PENDING = "SERVICE_PENDING",
  LOCATION_PENDING = "LOCATION_PENDING",
  TIME_SLOT_PENDING = "TIME_SLOT_PENDING",
  FINDING_IRONMAN = "FINDING_IRONMAN",
  PICKUP_PENDING = "PICKUP_PENDING",
  PICKUP_USER_NO_RESP = "PICKUP_USER_NO_RESP",
  PICKUP_USER_REJECTED = "PICKUP_USER_REJECTED",
  PICKUP_COMPLETE = "PICKUP_COMPLETE",
  WORK_IN_PROGRESS = "WORK_IN_PROGRESS",
  WORK_DONE = "WORK_DONE",
  TO_BE_DELIVERED = "TO_BE_DELIVERED",
  DELIVERY_PENDING = "DELIVERY_PENDING",
  DELIVERY_ATTEMPTED = "DELIVERY_ATTEMPTED",
  DELIVERED = "DELIVERED",
  CLOSED = "CLOSED",
}

export interface OrderItem {
  price_id: string;
  count: number;
  amount: number;
}

export interface OrderItemWithValues {
  service_name: string;
  dress_category: string;
  count: number;
  amount: number;
}
