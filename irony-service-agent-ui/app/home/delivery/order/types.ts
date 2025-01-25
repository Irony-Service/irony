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
