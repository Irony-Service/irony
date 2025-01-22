"use client";
import Image from "next/image";
import { useState } from "react";
import clsx from "clsx";

interface RowProps {
  services: string[];
  order: any;
  lastRow: boolean;
  onShowOrder: (order: any) => void;
}

export default function Row(props: RowProps) {
  const [error, setError] = useState("");

  const showOrder = () => {
    try {
      props.onShowOrder(props.order);
    } catch (err) {
      console.log(err);
      setError("Invalid credentials");
    }
  };

  return (
    <div>
      <div className={clsx("flex justify-between items-center bg-white h-10 px-4", { "border-b border-gray-300": !props.lastRow })}>
        <div className="w-[95%] flex justify-between">
          <div className="w-1/3 flex items-center gap-1">
            <Image src="/fluent-mdl2_shirt.svg" alt="Login" width={18} height={18} />
            <span>{props.order?.count_range_description}</span>
          </div>
          <div className="w-1/3 flex items-center gap-1">
            <Image src="/streamline_iron.svg" alt="Login" width={18} height={18} />
            <span>{props?.services}</span>
          </div>
          <div className="w-1/3 flex items-center gap-1">
            <Image src="/material-symbols-light_distance-outline.svg" alt="Login" width={18} height={18} />
            <span>{props.order?.distance}</span>
          </div>
        </div>
        <button onClick={showOrder}>
          <Image className="rounded-full bg-amber-300" src="/mingcute_right-line_black.svg" alt="Login" width={28} height={28} />
        </button>
      </div>
      {error && <p>{error}</p>}
    </div>
  );
}
