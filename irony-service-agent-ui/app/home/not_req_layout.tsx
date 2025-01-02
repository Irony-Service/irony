import Image from "next/image";

export default async function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto w-full max-w-[480px]">
      <div className="flex justify-between content-center py-3 my-2">
        <Image className="object-contain  text-amber-200" src="/mingcute_left-line.svg" alt="Login" width={28} height={28} />
        <h1 className="text-3xl font-bold text-sky-300">Work In Progess</h1>
        <Image className="object-contain  text-amber-200" src="/mingcute_right-line.svg" alt="Login" width={28} height={28} />
      </div>
      {children}
    </div>
  );
}
