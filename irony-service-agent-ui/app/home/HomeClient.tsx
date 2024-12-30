"use client";
import Image from "next/image";
import Row from "./Row";

interface HomeProps {
  data: unknown;
}

export default function HomeClient({ data }: HomeProps) {
  console.log(data);
  return (
    <div className="mx-auto w-full max-w-[480px]">
      <div className="flex justify-between content-center py-3 my-2">
        <Image className="object-contain  text-amber-200" src="/mingcute_left-line.svg" alt="Login" width={28} height={28} />
        <h1 className="text-3xl font-bold text-sky-300">Work In Progess</h1>
        <Image className="object-contain  text-amber-200" src="/mingcute_right-line.svg" alt="Login" width={28} height={28} />
      </div>
      <section className="bg-gray-100 py-4">
        <div className="w-[96%]  mx-auto">
          <h1 className="text-2xl  text-sky-300 font-normal mb-5 px-2">Mon, Dec 29 (16 Orders)</h1>
          <div className="flex flex-col text-gray-700 rounded-3xl overflow-hidden">
            <div className="flex justify-between items-center h-10 px-2 bg-amber-300">
              <h2 className="text-base">Slot : 7:00 am - 9:00 am (12 Orders)</h2>
            </div>

            <div className="text-xs">
              <Row data={{ count_range: "15 to 20", services: ["Wash & Iron"], distance: "1 Km" }} />
              <Row data={{ count_range: "15 to 20", services: ["Wash & Iron"], distance: "1 Km" }} />
              <Row data={{ count_range: "15 to 20", services: ["Wash & Iron"], distance: "1 Km" }} />
              <Row data={{ count_range: "15 to 20", services: ["Wash & Iron"], distance: "1 Km" }} lastRow={true} />
              {/* <div className="flex justify-between items-center bg-white h-10 px-2 border-b border-gray-300">
                <div className="w-4/5 flex justify-between">
                  <div className="flex items-center gap-1">
                    <Image src="/fluent-mdl2_shirt.svg" alt="Login" width={18} height={18} />
                    <span>15 to 20</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Image src="/streamline_iron.svg" alt="Login" width={18} height={18} />
                    <span>Wash & Iron</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Image src="/material-symbols-light_distance-outline.svg" alt="Login" width={18} height={18} />
                    <span>1 Km</span>
                  </div>
                </div>
                <button>
                  <Image className="rounded-full bg-amber-300" src="/mingcute_right-line_black.svg" alt="Login" width={28} height={28} />
                </button>
              </div>
              <div className="flex justify-between items-center bg-white h-10 px-2 border-b border-gray-300">
                <div className="w-4/5 flex justify-between">
                  <div className="flex items-center gap-1">
                    <Image src="/fluent-mdl2_shirt.svg" alt="Login" width={18} height={18} />
                    <span>15 to 20</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Image src="/streamline_iron.svg" alt="Login" width={18} height={18} />
                    <span>Wash & Iron</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Image src="/material-symbols-light_distance-outline.svg" alt="Login" width={18} height={18} />
                    <span>1 Km</span>
                  </div>
                </div>
                <button>
                  <Image className="rounded-full bg-amber-300" src="/mingcute_right-line_black.svg" alt="Login" width={28} height={28} />
                </button>
              </div>
              <div className="flex justify-between items-center bg-white h-10 px-2 border-b border-gray-300">
                <div className="w-4/5 flex justify-between">
                  <div className="flex items-center gap-1">
                    <Image src="/fluent-mdl2_shirt.svg" alt="Login" width={18} height={18} />
                    <span>15 to 20</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Image src="/streamline_iron.svg" alt="Login" width={18} height={18} />
                    <span>Wash & Iron</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Image src="/material-symbols-light_distance-outline.svg" alt="Login" width={18} height={18} />
                    <span>1 Km</span>
                  </div>
                </div>
                <button>
                  <Image className="rounded-full bg-amber-300" src="/mingcute_right-line_black.svg" alt="Login" width={28} height={28} />
                </button>
              </div>
              <div className="flex justify-between items-center bg-white h-10 px-2 border-b border-gray-300">
                <div className="w-4/5 flex justify-between">
                  <div className="flex items-center gap-1">
                    <Image src="/fluent-mdl2_shirt.svg" alt="Login" width={18} height={18} />
                    <span>15 to 20</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Image src="/streamline_iron.svg" alt="Login" width={18} height={18} />
                    <span>Wash & Iron</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Image src="/material-symbols-light_distance-outline.svg" alt="Login" width={18} height={18} />
                    <span>1 Km</span>
                  </div>
                </div>
                <button>
                  <Image className="rounded-full bg-amber-300" src="/mingcute_right-line_black.svg" alt="Login" width={28} height={28} />
                </button>
              </div>
              <div className="flex justify-between items-center bg-white h-10 px-2">
                <div className="w-4/5 flex justify-between">
                  <div className="flex items-center gap-1">
                    <Image src="/fluent-mdl2_shirt.svg" alt="Login" width={18} height={18} />
                    <span>15 to 20</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Image src="/streamline_iron.svg" alt="Login" width={18} height={18} />
                    <span>Wash & Iron</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Image src="/material-symbols-light_distance-outline.svg" alt="Login" width={18} height={18} />
                    <span>1 Km</span>
                  </div>
                </div>
                <button>
                  <Image className="rounded-full bg-amber-300" src="/mingcute_right-line_black.svg" alt="Login" width={28} height={28} />
                </button>
              </div> */}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
