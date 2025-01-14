"use client";
import Image from "next/image";
import { useState } from "react";
import clsx from "clsx";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface RowProps {
  data: {
    order: any;
    maps_link: string;
    delivery_type: string;
    count_range: string;
    services: string[];
    distance: string;
  };
  lastRow: boolean;
}

export default function DeliveryRow({ data, lastRow = false }: RowProps) {
  // console.log(data);
  const router = useRouter();
  const [error, setError] = useState("");

  const showOrder = async (e: React.FormEvent) => {
    e.preventDefault();

    router.push("/home/delivery/order");
    try {
    } catch (err) {
      console.log(err);
      setError("Invalid credentials");
    }
  };

  return (
    <div>
      <div className={clsx("flex justify-between items-center bg-white h-10 px-4", { "border-b border-gray-300": !lastRow })}>
        <div className="w-[80%] flex justify-between items-center">
          <div className="flex items-center gap-1">
            <Image src={`/carbon_delivery-${data.delivery_type?.includes("pickup") ? "add" : "minus"}.svg`} alt="Login" width={18} height={18} />
            <span>{data.delivery_type}</span>
          </div>
          <div className="flex items-center gap-1">
            <Image src="/fluent-mdl2_shirt.svg" alt="Login" width={18} height={18} />
            <span>{data.count_range}</span>
          </div>
          <div className="flex items-center gap-1">
            <Image src="/streamline_iron.svg" alt="Login" width={18} height={18} />
            <span>{data.services}</span>
          </div>
          <div className="flex items-center gap-1">
            <Image src="/material-symbols-light_distance-outline.svg" alt="Login" width={18} height={18} />
            <span>{data.distance}</span>
          </div>
        </div>
        <Link href={data.maps_link || ""} className="p-[6px] rounded-full bg-amber-300">
          <Image src="/maps_arrow.svg" alt="Login" width={16} height={16} />
        </Link>
        <button onClick={showOrder}>
          <Image className="rounded-full bg-amber-300" src="/mingcute_right-line_black.svg" alt="Login" width={28} height={28} />
        </button>
      </div>
      {error && <p>{error}</p>}
    </div>
  );
}
