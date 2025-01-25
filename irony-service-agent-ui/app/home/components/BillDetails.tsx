interface BillDetailsProps {
  orderItems: Array<{
    service: number;
    dress: number;
    count: number;
  }>;
  location_service_prices: any;
}

export default function BillDetails({ orderItems, location_service_prices }: BillDetailsProps) {
  return (
    <div className="flex flex-col">
      <div className="text-sm font-medium text-gray-700 mb-2">Bill Details:</div>
      <div className="border rounded p-3">
        {orderItems.map((item, index) => {
          const service = location_service_prices[item.service].service;
          const dress_type_obj = location_service_prices[item.service].prices[item.dress];
          if (!isNaN(item.count) && item.count > 0) {
            return (
              <div key={`bill-item-${index}`} className="flex justify-between mb-2">
                <div className="flex flex-col text-sm">
                  <span className="font-medium">
                    {service.service_name} • {dress_type_obj.category}
                  </span>
                  <span className="text-gray-500">
                    {item.count} items • ₹{dress_type_obj.price} each
                  </span>
                </div>
                <div className="text-sm font-medium">₹{(item.count * dress_type_obj.price).toFixed(2)}</div>
              </div>
            );
          }
        })}
        <div className="border-t mt-2 pt-2 flex justify-between">
          <div className="text-sm font-medium">Total</div>
          <div className="text-sm font-medium">
            ₹{orderItems.reduce((sum, item) => sum + Number(item.count) * location_service_prices[item.service].prices[item.dress]?.price, 0).toFixed(2)}
          </div>
        </div>
      </div>
    </div>
  );
}
