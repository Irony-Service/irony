import { cookies } from "next/headers";
import api from "../../utils/axios";
import HomeClient from "./HomeClient";

export default async function Home() {
  const response = await fetchHomeData();

  return <HomeClient data={response}></HomeClient>;

  async function fetchHomeData() {
    const cookieStore = await cookies();
    const authToken = cookieStore.get("auth_token");
    console.log("This is auth_token cookie: ", authToken);
    const response = await api.get("/agentOrdersByStatusGroupByDateAndTimeSlot", {
      params: {
        order_status: "FINDING_IRONMAN,PICKUP_PENDING,WORK_IN_PROGRESS,DELIVERY_PENDING",
      },
    });
    return response.data;
  }
}
