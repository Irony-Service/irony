import { cookies } from "next/headers";
import api from "../../../utils/axios";
import HomeClient from "./ClientAgent";

export default async function Home() {
  const response = await fetchHomeData();

  return <HomeClient responses={response}></HomeClient>;

  async function fetchHomeData() {
    const cookieStore = await cookies();
    const authToken = cookieStore.get("auth_token");
    console.log("This is auth_token cookie: ", authToken);

    // const url = new URL("/agentOrdersByStatusGroupByDateAndTimeSlot");
    // url.search = new URLSearchParams({
    //   order_status: "FINDING_IRONMAN,PICKUP_PENDING,WORK_IN_PROGRESS,DELIVERY_PENDING",
    // }).toString();

    const [ordersResponse, prices_response] = await Promise.all([
      api(
        `/agentOrdersByStatusGroupByStatusAndDateAndTimeSlot`,
        {
          method: "GET",
          cache: "no-cache",
        },
        {
          order_status: "FINDING_IRONMAN,PICKUP_PENDING,WORK_IN_PROGRESS,DELIVERY_PENDING",
        }
      ),
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
