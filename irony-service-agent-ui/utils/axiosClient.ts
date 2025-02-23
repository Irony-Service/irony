// Get the API base URL from the environment variable
// const apiBaseUrl: string = "http://irony.store:8000/api/ironman";
const apiBaseUrl: string = process.env.NEXT_PUBLIC_CLIENT_API_URL ? `${process.env.NEXT_PUBLIC_CLIENT_API_URL}/api` : "";

if (!apiBaseUrl) {
  throw new Error("NEXT_PUBLIC_API_URL is not defined in the environment variables");
}

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
    cache: options.cache || "no-store", // Add default cache option
  };

  const response = await fetch(url.toString(), fetchOptions);

  if (!response.ok) {
    const error = await response.json();
    const errorMessage = typeof error.detail === "object" ? JSON.stringify(error.detail) : error.detail;
    throw new Error(errorMessage || "An error occurred");
  }

  return response.json();
}

// Helper methods for common HTTP methods with cache option
const apiClient = {
  get: <T>(endpoint: string, queryParams?: Record<string, string | number | boolean>, options?: RequestInit) => fetchApiClient<T>(endpoint, { method: "GET", ...options }, queryParams),

  post: <T>(endpoint: string, data?: any, options?: RequestInit) =>
    fetchApiClient<T>(endpoint, {
      method: "POST",
      body: JSON.stringify(data),
      ...options,
    }),

  put: <T>(endpoint: string, data?: any, options?: RequestInit) =>
    fetchApiClient<T>(endpoint, {
      method: "PUT",
      body: JSON.stringify(data),
      ...options,
    }),

  delete: <T>(endpoint: string, options?: RequestInit) => fetchApiClient<T>(endpoint, { method: "DELETE", ...options }),
};

export default apiClient;
