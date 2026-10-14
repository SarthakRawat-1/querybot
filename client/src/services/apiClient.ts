import axios, { type AxiosInstance } from 'axios';
import { config } from '@/config/env';
import type { ApiError } from '@/types/api';

/**
 * Shared axios instances.
 *
 * Both instances remain available for compatibility with dormant auth modules;
 * application requests are public and do not carry a session.
 */
const createInstance = (): AxiosInstance =>
  axios.create({
    baseURL: config.API_BASE_URL,
    headers: { 'Content-Type': 'application/json' },
    withCredentials: true,
  });

export const api = createInstance();
export const plainApi = createInstance();

/** Extract a message suitable for showing the user from any thrown value. */
export const getErrorMessage = (error: unknown, fallback = 'Something went wrong'): string => {
  if (axios.isAxiosError<ApiError>(error)) {
    if (!error.response) {
      return 'Could not reach the server. Check that it is running and try again.';
    }

    const data = error.response.data;

    // Field-level validation errors are more useful than the generic message.
    if (data?.errors) {
      const details = Object.entries(data.errors)
        .map(([field, messages]) => `${field}: ${messages.join(', ')}`)
        .join('\n');
      if (details) return details;
    }

    return data?.message || fallback;
  }

  return error instanceof Error ? error.message : fallback;
};
