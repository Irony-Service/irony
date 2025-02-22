import { OrderItemWithValues } from "../types/types";

interface BillDetailsWithValuesProps {
  orderItems: OrderItemWithValues[];
}

export default function BillDetailsWithValues({ orderItems }: BillDetailsWithValuesProps) {
  return (
    <div className="flex flex-col">
      <div className="text-sm font-medium text-gray-700 mb-2">Bill Details:</div>
      <div className="border rounded p-3">
        {orderItems.map((item, index) => {
          if (!isNaN(item.count) && item.count > 0) {
            return (
              <div key={`bill-item-${index}`} className="flex justify-between mb-2">
                <div className="flex flex-col text-sm">
                  <span className="font-medium">
                    {item.service_name} • {item.dress_category}
                  </span>
                  <span className="text-gray-500">
                    {item.count} items • ₹{item.amount / item.count} each
                  </span>
                </div>
                <div className="text-sm font-medium">₹{item.amount}</div>
              </div>
            );
          }
        })}
        <div className="border-t mt-2 pt-2 flex justify-between">
          <div className="text-sm font-medium">Total</div>
          <div className="text-sm font-medium">
            ₹{orderItems.reduce((sum, item) => sum + item.amount, 0).toFixed(2)}
          </div>
        </div>
      </div>
    </div>
  );
}
