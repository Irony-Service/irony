import LayoutClient from "./LayoutClient";

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto w-full max-w-[480px]">
      {children} <LayoutClient></LayoutClient>
    </div>
  );
}
