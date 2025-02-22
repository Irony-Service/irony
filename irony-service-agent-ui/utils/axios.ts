import { cookies } from "next/headers";
import { redirect } from "next/navigation";

const apiBaseUrl: string = process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/api/ironman` : "";

if (!apiBaseUrl) {
  throw new Error("NEXT_PUBLIC_API_URL is not defined in the environment variables");
}

async function fetchApi<T>(endpoint: string, options: RequestInit = {}, queryParams?: Record<string, string | number | boolean>): Promise<T> {
  const url = new URL(`${apiBaseUrl}${endpoint}`);
  if (queryParams) {
    Object.entries(queryParams).forEach(([key, value]) => {
      url.searchParams.append(key, String(value));
    });
  }

  const cookieHeader = (await cookies()).toString();

  const fetchOptions: RequestInit = {
    ...options,
    headers: {
      ...options.headers,
      "Content-Type": "application/json",
      Cookie: cookieHeader,
    },
    credentials: "include",
    cache: options.cache || "no-store", // Add default cache option
  };

  const response = await fetch(url.toString(), fetchOptions);

  if (!response.ok) {
    if (response.status === 401) {
      redirect("/login");
    }
    const error = await response.json();
    const errorMessage = typeof error.detail === "object" ? JSON.stringify(error.detail) : error.detail;
    throw new Error(errorMessage || "An error occurred");
  }

  return response.json();
}

// Helper methods for common HTTP methods, similar to axiosClient
const axios = {
  get: <T>(endpoint: string, queryParams?: Record<string, string | number | boolean>, options?: RequestInit) => fetchApi<T>(endpoint, { method: "GET", ...options }, queryParams),

  post: <T>(endpoint: string, data?: any, options?: RequestInit) =>
    fetchApi<T>(endpoint, {
      method: "POST",
      body: JSON.stringify(data),
      ...options,
    }),

  put: <T>(endpoint: string, data?: any, options?: RequestInit) =>
    fetchApi<T>(endpoint, {
      method: "PUT",
      body: JSON.stringify(data),
      ...options,
    }),

  delete: <T>(endpoint: string, options?: RequestInit) => fetchApi<T>(endpoint, { method: "DELETE", ...options }),
};

export default axios;
