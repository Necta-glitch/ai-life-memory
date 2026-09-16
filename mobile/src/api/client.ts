import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { API_BASE_URL } from '@/constants/api';
import { Platform } from 'react-native';

/**
 * Creates and configures the Axios instance for API requests.
 * Reads the base URL from EXPO_PUBLIC_API_URL environment variable.
 * For development, falls back to platform-specific localhost URLs.
 */
function createApiClient(): AxiosInstance {
  // Determine base URL with platform-specific fallbacks
  const getBaseURL = (): string => {
    // Check for explicit environment variable first
    const envUrl = process.env.EXPO_PUBLIC_API_URL;
    if (envUrl) {
      return envUrl;
    }

    // Platform-specific fallbacks for local development
    // These are NOT for production - only for local development
    if (typeof navigator !== 'undefined') {
      // Running in browser/web
      return 'http://localhost:8000';
    }
    
    // React Native - check platform
    if (Platform.OS === 'ios') {
      // iOS Simulator can use localhost
      return 'http://localhost:8000';
    } else if (Platform.OS === 'android') {
      // Android emulator uses 10.0.2.2 to reach host localhost
      return 'http://10.0.2.2:8000';
    }
    
    // Default fallback
    return 'http://localhost:8000';
  };

  const client: AxiosInstance = axios.create({
    baseURL: API_BASE_URL || getBaseURL(),
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor - add auth headers if needed
  client.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      // Add X-User-ID header for temporary development authentication
      config.headers['X-User-ID'] = 'dev-user';
      
      // Future: Add auth token here when authentication is implemented
      // const token = await getAuthToken();
      // if (token) {
      //   config.headers.Authorization = `Bearer ${token}`;
      // }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor for error handling
  client.interceptors.response.use(
    (response) => response,
    (error) => {
      // Handle common errors
      if (error.response) {
        // Server responded with error status
        const status = error.response.status;
        if (status === 401) {
          // Unauthorized - could trigger logout
          // TODO: Handle auth redirect when auth is implemented
        } else if (status === 404) {
          // Not found
        } else if (status >= 500) {
          // Server error
        }
      } else if (error.request) {
        // Network error - no response received
        console.warn('Network error - no response from server');
      } else {
        // Request setup error
      }
      return Promise.reject(error);
    }
  );

  return client;
}

// Create and export the singleton API client
export const apiClient = createApiClient();

// Export a function to get the client (useful for testing)
export const getApiClient = (): ReturnType<typeof createApiClient> => {
  return apiClient;
};

// Type-safe API methods wrapper - re-export axios methods with proper typing
export const api = apiClient;