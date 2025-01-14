import { cookies } from "next/headers";
import api from "../../../utils/axios";
import DeliveryHomeClient from "./DeliveryHomeClient";

export default async function Home() {
  const response = await fetchHomeData();

  return <DeliveryHomeClient data={response}></DeliveryHomeClient>;

  async function fetchHomeData() {
    const cookieStore = await cookies();
    const authToken = cookieStore.get("auth_token");
    console.log("This is auth_token cookie: ", authToken);

    // const url = new URL("/agentOrdersByStatusGroupByDateAndTimeSlot");
    // url.search = new URLSearchParams({
    //   order_status: "FINDING_IRONMAN,PICKUP_PENDING,WORK_IN_PROGRESS,DELIVERY_PENDING",
    // }).toString();

    const response = await api(`/agentOrdersByStatusGroupByDateAndTimeSlot`, {
      method: "GET",
      cache: "no-cache",
    });
    return response;
  }
}
