import { cookies } from "next/headers";

const apiBaseUrl: string = "http://localhost:8000/api/ironman";

if (!apiBaseUrl) {
  throw new Error("NEXT_PUBLIC_API_URL is not defined in the environment variables");
}

export default async function fetchApi<T>(endpoint: string, options: RequestInit = {}, queryParams?: Record<string, string | number | boolean>): Promise<T> {
  // Construct the URL with query parameters
  const url = new URL(`${apiBaseUrl}${endpoint}`);
  if (queryParams) {
    Object.entries(queryParams).forEach(([key, value]) => {
      url.searchParams.append(key, String(value));
    });
  }

  // Retrieve cookies in server-side context
  const cookieHeader = (await cookies()).toString();

  const fetchOptions: RequestInit = {
    ...options,
    headers: {
      ...options.headers,
      "Content-Type": "application/json",
      Cookie: cookieHeader,
    },
    credentials: "include",
  };

  const response = await fetch(url.toString(), fetchOptions);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || "An error occurred");
  }

  return response.json();
}
