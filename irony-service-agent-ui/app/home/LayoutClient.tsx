"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import Image from "next/image";

const links = [
  { name: "Home Agent", href: "/home/agent" },
  {
    name: "Home Delivery",
    href: "/home/delivery",
  },
];

export default function LayoutClient() {
  const pathname = usePathname();
  console.log("This is pathname: ", pathname);
  return (
    <div className="sticky bottom-0 left-0 w-full h-12 flex mt-2">
      <div className={`w-1/2 h-full rounded-tl-2xl shadow-2xl shadow-gray-900  ${pathname === links[0].href ? "bg-gray-800" : "bg-white"}`}>
        <Link key={links[0].name} href={links[0].href} className="h-full flex justify-center content-center">
          <Image src={`${pathname === links[0].href ? "/material-symbols_iron-outline-rounded.svg" : "/material-symbols_iron-outline-rounded_black.svg"}`} alt="Previous" width={28} height={28} />
        </Link>
      </div>
      <div className={`w-1/2 h-full rounded-tr-2xl shadow-2xl shadow-gray-900 ${pathname === links[1].href ? "bg-gray-800" : "bg-white"}`}>
        <Link key={links[1].name} href={links[1].href} className="h-full flex justify-center content-center">
          <Image src={`${pathname === links[1].href ? "/ic_outline-delivery-dining.svg" : "/ic_outline-delivery-dining_black.svg"}`} alt="Previous" width={28} height={28} />
        </Link>
      </div>
    </div>
  );
}
