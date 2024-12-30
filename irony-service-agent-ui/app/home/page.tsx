import api from "../../utils/axios";
import HomeClient from "./HomeClient";

export default async function Home() {
  const data = await fetchHomeData();
  console.log(data);

  return <HomeClient data={data}></HomeClient>;

  async function fetchHomeData() {
    const response = await api.get("/fetchOrders");
    const { data } = response.data;
    return data;
  }
}
