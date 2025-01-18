import { cookies } from "next/headers";
import api from "../../../utils/axios";
import DeliveryHomeClient from "./Client";

export default async function Home() {
  const response = await fetchHomeData();

  return <DeliveryHomeClient responses={response}></DeliveryHomeClient>;

  async function fetchHomeData() {
    const cookieStore = await cookies();
    const authToken = cookieStore.get("auth_token");
    console.log("This is auth_token cookie: ", authToken);

    // const url = new URL("/agentOrdersByStatusGroupByDateAndTimeSlot");
    // url.search = new URLSearchParams({
    //   order_status: "FINDING_IRONMAN,PICKUP_PENDING,WORK_IN_PROGRESS,DELIVERY_PENDING",
    // }).toString();

    const [ordersResponse, prices_response] = await Promise.all([
      api(`/agentOrdersByStatusGroupByDateAndTimeSlot`, {
        method: "GET",
        cache: "no-cache",
      }),
      api(`/servicePricesForServiceLocations`, {
        method: "GET",
        cache: "no-cache",
      }),
    ]);

    const response = {
      orders: ordersResponse,
      service_location_prices: prices_response,
    };

    return response;
  }
}
