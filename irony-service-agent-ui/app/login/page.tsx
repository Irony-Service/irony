"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import Image from "next/image";
import apiClient from "../../utils/axiosClient";

export default function Login() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    mobile: "",
    password: "",
  });
  const [error, setError] = useState("");

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    setError(""); // Clear error when user types
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      const response = await apiClient.post<any>("/login", formData, { cache: "no-store" });
      router.push("/home/agent");
    } catch (err: any) {
      setError(err.message || "Invalid credentials");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center">
      <div className="max-w-md w-full mx-auto p-6">
        <div className="bg-white rounded-xl shadow-lg p-8">
          {/* Logo/Header */}
          <div className="text-center mb-8">
            <Image src="/logo.svg" alt="Logo" width={64} height={64} className="mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-800">Agent Login</h2>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
            {/* Mobile Input */}
            <div>
              <label htmlFor="mobile" className="block text-sm font-medium text-gray-700 mb-2">
                Mobile Number
              </label>
              <input
                type="tel"
                id="mobile"
                name="mobile"
                value={formData.mobile}
                onChange={handleInputChange}
                className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:outline-none focus:border-amber-300 transition-colors"
                placeholder="Enter your mobile number"
                required
              />
            </div>

            {/* Password Input */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:outline-none focus:border-amber-300 transition-colors"
                placeholder="Enter your password"
                required
              />
            </div>

            {/* Error Message */}
            {error && <div className="p-3 rounded-lg bg-red-50 text-red-600 text-sm">{error}</div>}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className={`w-full py-3 px-4 rounded-lg text-white font-medium transition-colors
                ${isLoading ? "bg-gray-400 cursor-not-allowed" : "bg-amber-400 hover:bg-amber-500"}`}
            >
              {isLoading ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Logging in...</span>
                </div>
              ) : (
                "Login"
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
