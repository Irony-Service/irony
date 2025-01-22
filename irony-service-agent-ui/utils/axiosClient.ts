// utils/axios.ts
import axios from "axios";

// Get the API base URL from the environment variable
const apiBaseUrl: string = "http://localhost:8000/api/ironman";

if (!apiBaseUrl) {
  throw new Error("NEXT_PUBLIC_API_URL is not defined in the environment variables");
}

// Create an instance of Axios with global configuration
const api = axios.create({
  baseURL: apiBaseUrl, // Using the environment variable here
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

async function fetchApiClient<T>(endpoint: string, options: RequestInit = {}, queryParams?: Record<string, string | number | boolean>): Promise<T> {
  // Construct the URL with query parameters
  const url = new URL(`${apiBaseUrl}${endpoint}`);
  if (queryParams) {
    Object.entries(queryParams).forEach(([key, value]) => {
      url.searchParams.append(key, String(value));
    });
  }

  const fetchOptions: RequestInit = {
    ...options,
    headers: {
      ...options.headers,
      "Content-Type": "application/json",
    },
    credentials: "include", // This ensures cookies are sent with requests
  };

  const response = await fetch(url.toString(), fetchOptions);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || "An error occurred");
  }

  return response.json();
}

// Helper methods for common HTTP methods
const apiClient = {
  get: <T>(endpoint: string, queryParams?: Record<string, string | number | boolean>) => fetchApiClient<T>(endpoint, { method: "GET" }, queryParams),

  post: <T>(endpoint: string, data?: any) =>
    fetchApiClient<T>(endpoint, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  put: <T>(endpoint: string, data?: any) =>
    fetchApiClient<T>(endpoint, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: <T>(endpoint: string) => fetchApiClient<T>(endpoint, { method: "DELETE" }),
};

export default apiClient;
