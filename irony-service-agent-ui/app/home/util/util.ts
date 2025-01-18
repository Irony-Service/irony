import { format, parse } from "date-fns";

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
}
