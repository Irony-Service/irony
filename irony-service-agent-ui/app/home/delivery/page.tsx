import { cookies } from "next/headers";
import axios from "../../../utils/axios";
import DeliveryHomeClient from "./Client";

export default async function Home() {
  const response = await fetchHomeData();
  return <DeliveryHomeClient responses={response}></DeliveryHomeClient>;
}

async function fetchHomeData() {
  const cookieStore = await cookies();
  const authToken = cookieStore.get("auth_token");
  console.log("This is auth_token cookie: ", authToken);

  const [ordersResponse, pricesResponse] = await Promise.all([
    axios.get(
      "/agentOrdersByStatusGroupByDateAndTimeSlot",
      undefined,
      { cache: "no-store" }
    ),
    axios.get(
      "/servicePricesForServiceLocations",
      undefined,
      { cache: "no-store" }
    ),
  ]);

  return {
    orders: ordersResponse,
    service_location_prices: pricesResponse,
  };
}
