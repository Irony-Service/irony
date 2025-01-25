// pages/login.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "../../utils/axiosClient";
import { LoginButton } from "./components/LoginButton";
import Link from "next/link";

export default function Login() {
  const router = useRouter();
  const [mobile, setMobile] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await api.post<any>("/login", { mobile, password });
      console.log(response);
      console.log(response.data);

      // const { token } = response.data;

      // Store token in localStorage
      // localStorage.setItem("auth_token", token);

      // Redirect to home page upon success
      router.push("/home/agent");
    } catch (err) {
      console.log(err);
      setError("Invalid credentials");
    }
  };

  return (
    <div className="flex overflow-hidden flex-col px-3.5 pt-60 pb-96 mx-auto w-full bg-amber-100 max-w-[480px]">
      <h1 className="self-start text-3xl font-bold text-sky-300 mb-5">Login</h1>
      <form onSubmit={handleLogin}>
        <div className="relative mb-8">
          <label htmlFor="mobile" className="sr-only">
            Mobile
          </label>
          <input
            type="tel"
            id="mobile"
            placeholder="Mobile"
            value={mobile}
            onChange={(e) => setMobile(e.target.value)}
            className="px-4 py-3  w-full max-w-full text-xs whitespace-nowrap bg-white rounded-3xl text-neutral-400"
          />
        </div>

        <div className="relative mb-8">
          <label htmlFor="password" className="sr-only">
            Password
          </label>
          <input
            type="password"
            id="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="px-4 py-3  w-full max-w-full text-xs whitespace-nowrap bg-white rounded-3xl text-neutral-400"
          />
        </div>
        {error && <p>{error}</p>}
        <LoginButton />
      </form>
    </div>

    // <div>
    //   <h1>Login</h1>
    //   <form onSubmit={handleLogin}>
    //     <input
    //       type="text"
    //       placeholder="Mobile"
    //       value={mobile}
    //       onChange={(e) => setMobile(e.target.value)}
    //     />
    //     <input
    //       type="password"
    //       placeholder="Password"
    //       value={password}
    //       onChange={(e) => setPassword(e.target.value)}
    //     />
    //     {error && <p>{error}</p>}
    //     <button type="submit">Login</button>
    //   </form>
    // </div>
  );
}
