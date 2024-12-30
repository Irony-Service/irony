// utils/axios.ts
import axios from "axios";

// Get the API base URL from the environment variable
const apiBaseUrl: string = "http://127.0.0.1:8000/api/ironman";

if (!apiBaseUrl) {
  throw new Error("NEXT_PUBLIC_API_URL is not defined in the environment variables");
}

// Create an instance of Axios with global configuration
const api = axios.create({
  baseURL: apiBaseUrl, // Using the environment variable here
  headers: {
    "Content-Type": "application/json",
  },
});

// Intercept requests to add Authorization header if token exists
api.interceptors.request.use(
  (config) => {
    // const token = localStorage.getItem("auth_token"); // Get token from localStorage
    const token = "123";
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`; // Add Authorization header
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default api;
