import * as React from "react";
import { ServiceBlockProps } from "./types";

export default function ServiceBlock({}: ServiceBlockProps) {
  return (
    <div className="flex overflow-hidden flex-col p-2 w-full text-xs font-medium text-gray-700 bg-amber-300 rounded-xl">
      <div className="flex overflow-hidden justify-between items-center w-full">
        <div className="flex-1 shrink self-stretch my-auto basis-0 max-w-[60px]">Service </div>
        <div className="flex flex-1 shrink self-stretch my-auto h-6 bg-white rounded-xl basis-0 min-w-[240px] w-[244px]">
          <select className="w-full h-full px-2 bg-transparent border-none outline-none">
            <option value="option1">Option 1</option>
            <option value="option2">Option 2</option>
            <option value="option3">Option 3</option>
          </select>
        </div>
      </div>
      <div className="flex overflow-hidden justify-between items-center mt-2.5 w-full whitespace-nowrap">
        <div className="flex-1 shrink self-stretch my-auto basis-0 max-w-[60px]">Dress</div>
        <div className="flex flex-1 shrink self-stretch my-auto h-6 bg-white rounded-xl basis-0 min-w-[240px] w-[244px]">
          <select className="w-full h-full px-2 bg-transparent border-none outline-none">
            <option value="option1">Option 1</option>
            <option value="option2">Option 2</option>
            <option value="option3">Option 3</option>
          </select>
        </div>
      </div>
      <div className="flex overflow-hidden justify-between items-center mt-2.5 w-full">
        <div className="flex-1 shrink self-stretch my-auto basis-0 max-w-[60px]">Count </div>
        <div className="flex flex-1 shrink self-stretch my-auto h-6 bg-white rounded-xl basis-0 min-w-[240px] w-[244px]">
          <input type="number" className="w-full h-full px-2 text-center bg-transparent border-none outline-none" />
        </div>
      </div>
    </div>
  );
}
