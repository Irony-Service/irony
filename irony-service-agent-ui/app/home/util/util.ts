import { format, parse } from "date-fns";
import { ServicePrices } from "../types/types";

type ServiceLocationPrices = {
  [key: string]: ServicePrices[];
};

export function greet(name: string): string {
  return `Hello, ${name}!`;
}

export function getOrdersInDate(time_slots: any[]): number {
  return time_slots.reduce((totalOrders, timeSlot) => totalOrders + timeSlot.orders.length, 0);
}

export function formatDate(inputDate: string): string {
  const date = parse(inputDate, "yyyy-MM-dd'T'HH:mm:ss", new Date());
  return format(date, "eee, d MMM");
}

export function getPriceServiceNameMaps(service_locations_prices: ServiceLocationPrices): { priceServiceMap: Map<string, string>; priceNameMap: Map<string, string> } {
    const localPriceServiceMap = new Map<string, string>();
    const localPriceNameMap = new Map<string, string>();
    Object.values(service_locations_prices).forEach((servicePrices) => {
      servicePrices.forEach((price) => {
        if (price.prices && price.service) {
          price.prices.forEach((p) => {
            localPriceNameMap.set(p._id, p.category);
            localPriceServiceMap.set(p._id, price.service.service_name);
          });
        }
      });
    });
    return {priceServiceMap: localPriceServiceMap, priceNameMap: localPriceNameMap};
}

export default class Util {
  static greet(name: string): string {
    return greet(name);
  }

  static getOrdersInDate(time_slots: any[]): number {
    return getOrdersInDate(time_slots);
  }

  static formatDate(inputDate: string): string {
    return formatDate(inputDate);
  }

  static getPriceServiceNameMaps(service_locations_prices: ServiceLocationPrices): { priceServiceMap: Map<string, string>; priceNameMap: Map<string, string> } {
    return getPriceServiceNameMaps(service_locations_prices);
  }
}
