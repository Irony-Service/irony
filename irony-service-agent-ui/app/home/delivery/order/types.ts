import { OrderDetailsProps } from "./types";
export interface ServiceBlockProps {
  service: string;
  dress: string;
  count: string;
}

export interface OrderDetailsProps {
  orderId: string;
  customerName: string;
  phoneNumber: string;
  countRange: string;
  services: ServiceBlockProps[];
}

export interface OrderDetailsProps1 {
  order: any;
}
