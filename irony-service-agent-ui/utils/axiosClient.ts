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

export default api;
