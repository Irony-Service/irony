import { cookies } from "next/headers";
import axios from "../../../utils/axios";
import HomeClient from "./ClientAgent";

export default async function Home() {
  const response = await fetchHomeData();
  return <HomeClient responses={response}></HomeClient>;
}

async function fetchHomeData() {
  const cookieStore = await cookies();
  const authToken = cookieStore.get("auth_token");
  console.log("This is auth_token cookie: ", authToken);

  const [ordersResponse, prices_response] = await Promise.all([
    axios.get(
      "/agentOrdersByStatusGroupByStatusAndDateAndTimeSlot",
      {
        order_status: "PICKUP_PENDING,WORK_IN_PROGRESS,DELIVERY_PENDING",
      },
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
    service_location_prices: prices_response,
  };
}
