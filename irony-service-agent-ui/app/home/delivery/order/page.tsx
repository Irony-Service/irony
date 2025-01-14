import React from "react";
import OrderDetails from "./OrderDetails";
import { ServiceBlockProps } from "./types";
const OrderPage = () => {
  const order = {
    _id: "67554df7197512caeb39d079",
    simple_id: null,
    user_id: "66c08db86a6257894b647db9",
    user: null,
    user_wa_id: "919381792043",
    order_items: null,
    service_location_id: "66bb88a947ce9461aaf6448d",
    service_location: null,
    services: [
      {
        _id: "66cb626be1ead44b7cfb43d6",
        service_category: "Clothes",
        service_type: "Laundry",
        service_name: "Iron",
        call_to_action_key: "SERVICE_ID_1",
      },
    ],
    count_range: "CLOTHES_COUNT_15_TO_25",
    count_range_description: "15-25",
    location: {
      _id: "67554e0f197512caeb39d07a",
      user: "919381792043",
      nickname: null,
      address: null,
      location: {
        type: "Point",
        coordinates: [17.4401319, 78.3304159],
      },
      url: null,
      created_on: "2024-12-08T13:13:11.435000",
      last_used: "2024-12-08T13:13:11.435000",
    },
    existing_location: null,
    trigger_order_request_at: null,
    time_slot: "TIME_SLOT_ID_3",
    time_slot_description: "Evening 4PM to 7PM",
    total_price: null,
    total_count: null,
    order_status: [
      {
        _id: null,
        order_id: "67554df7197512caeb39d079",
        status: "PICKUP_PENDING",
        created_on: "2024-12-08T13:13:25.491000",
        updated_on: null,
      },
      {
        _id: null,
        order_id: null,
        status: "FINDING_IRONMAN",
        created_on: "2024-12-08T13:13:23.360000",
        updated_on: null,
      },
      {
        _id: null,
        order_id: null,
        status: "TIME_SLOT_PENDING",
        created_on: "2024-12-08T13:13:11.883000",
        updated_on: null,
      },
      {
        _id: null,
        order_id: null,
        status: "LOCATION_PENDING",
        created_on: "2024-12-08T13:12:59.262000",
        updated_on: null,
      },
      {
        _id: null,
        order_id: null,
        status: "SERVICE_PENDING",
        created_on: "2024-12-08T13:12:47.077000",
        updated_on: null,
      },
    ],
    is_active: false,
    pickup_agent_id: null,
    drop_agent_id: null,
    created_on: "2024-12-08T13:12:47.079000",
    updated_on: "2024-12-08T13:13:25.491000",
    pick_up_time: {
      start: "2024-12-08T16:00:00",
      end: "2024-12-08T19:00:00",
    },
    auto_alloted: null,
    delivery_type: "Pickup",
    maps_link: "https://www.google.com/maps/search/?api=1&query=17.4401319,78.3304159",
  };

  return <OrderDetails order={order}></OrderDetails>;
};

export default OrderPage;
