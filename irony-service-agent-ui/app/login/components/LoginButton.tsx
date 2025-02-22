import Image from "next/image";

export const LoginButton: React.FC = () => {
  return (
    <button className="flex flex-col justify-center items-center px-20 py-3.5 bg-amber-200 rounded-3xl w-full" type="submit">
      <Image className="object-contain" src="/service/arrow_1.svg" alt="Login" width={100} height={20} />
    </button>
  );
};
