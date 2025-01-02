import * as React from "react";
import { InputFieldProps } from "./types";

export const InputField: React.FC<InputFieldProps> = ({ placeholder, type, id }) => {
  return (
    <div className="relative mb-8">
      <label htmlFor={id} className="sr-only">
        {placeholder}
      </label>
      <input type={type} id={id} placeholder={placeholder} className="px-4 py-3 w-[380px] max-w-full text-xs whitespace-nowrap bg-white rounded-3xl text-neutral-400" />
    </div>
  );
};
