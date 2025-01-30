"use client";
import clsx from "clsx";
import Image from "next/image";
import Link from "next/link";
import { useState } from "react";

interface RowProps {
  order: any;
  services: string[];
  lastRow: boolean;
  onShowOrder: (order: any) => void;
}

export default function DeliveryRow(props: RowProps) {
  // const router = useRouter();
  const [error, setError] = useState("");

  const showOrderDetails = () => {
    try {
      props.onShowOrder(props.order);
    } catch (err) {
      console.log(err);
      setError("Invalid credentials");
    }
  };

  return (
    <div>
      <div
        className={clsx("flex justify-between items-center bg-white h-10 px-4", {
          "border-b border-gray-300": !props.lastRow,
        })}
      >
        <div className="w-[80%] flex justify-between items-center">
          <div className="flex items-center gap-1">
            <Image
              src={`/carbon_delivery-${props.order?.delivery_type?.includes("pickup") ? "add" : "minus"}.svg`}
              alt="Login"
              width={18}
              height={18}
            />
            <span>{props.order?.delivery_type}</span>
          </div>
          <div className="flex items-center gap-1">
            <Image src="/fluent-mdl2_shirt.svg" alt="Login" width={18} height={18} />
            <span>{props.order?.count_range_description}</span>
          </div>
          <div className="flex items-center gap-1">
            <Image src="/streamline_iron.svg" alt="Login" width={18} height={18} />
            <span>{props.services}</span>
          </div>
          <div className="flex items-center gap-1">
            <Image src="/material-symbols-light_distance-outline.svg" alt="Login" width={18} height={18} />
            <span>{props.order?.distance}</span>
          </div>
        </div>
        <Link href={props.order?.maps_link || ""} className="p-[6px] rounded-full bg-amber-300">
          <Image src="/maps_arrow.svg" alt="Login" width={16} height={16} />
        </Link>
        <button onClick={showOrderDetails}>
          <Image
            className="rounded-full bg-amber-300"
            src="/mingcute_right-line_black.svg"
            alt="Login"
            width={28}
            height={28}
          />
        </button>
      </div>
      {error && <p>{error}</p>}
    </div>
  );
}
