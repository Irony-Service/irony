export interface ServiceBlockProps {
  location_service_prices: ServicePrices[];
  service: string;
  dress: string;
  count: string;
  onClose: (index: number) => void;
  onInputChange: (index: number, key: keyof OrderItem, value: string) => void;
  index: number; // Add this line
}

export interface Service {
  id: string;
  service_category: string;
  service_type: string;
  service_name: string;
  call_to_action_key: string;
}
export interface Price {
  id: string;
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
  onClose: () => void;
}

export interface OrderItem {
  service: string;
  dress: string;
  count: string;
}
