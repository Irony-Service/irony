interface ServiceItem {
    price_id: string;
    count: number;
    amount: number;
  }

  interface ServicesListProps {
    orderItems: ServiceItem[];
    priceServiceMap: Map<string, string>;
    priceNameMap: Map<string, string>;
  }

  export default function OrderServicesList({ orderItems, priceServiceMap, priceNameMap }: ServicesListProps) {
    return (
      <div>
        <div className="text-lg font-semibold text-gray-700 mb-4">Services</div>
        <div className="space-y-3">
          {orderItems.map((item, index) => (
            <div key={index} className="bg-gray-50 p-4 rounded-lg">
              <div className="grid grid-cols-3 gap-2 ">
                <div>
                  <span className="text-gray-500 text-sm">Service:</span>
                  <p className="font-medium">{priceServiceMap.get(item.price_id)}</p>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">Category:</span>
                  <p className="font-medium">{priceNameMap.get(item.price_id)}</p>
                </div>
                <div className="text-center">
                  <span className="text-gray-500 text-sm">Count:</span>
                  <p className="font-medium">{item.count}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }