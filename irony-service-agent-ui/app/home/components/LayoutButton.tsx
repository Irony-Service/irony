"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import Image from "next/image";

type LayoutButtonProps = {
  href: string;
  icon_paths: string[];
};

export default function LayoutButton({ href, icon_paths }: LayoutButtonProps) {
  const pathname = usePathname();

  return (
    <div className={`w-1/2 h-full rounded-tl-2xl ${pathname === href ? "bg-gray-800" : "bg-white"}`}>
      <Link href={href} className="h-full flex justify-center content-center">
        <Image src={`${pathname === href ? icon_paths[0] : icon_paths[1]}`} alt="Previous" width={28} height={28} />
      </Link>
    </div>
  );
}
