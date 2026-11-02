// Shared by the server (calling the SplitBill API) and the browser (calling this
// app's Route Handlers), so both turn HTTP responses into the same value.

import axios, { type AxiosInstance } from "axios";

/**
 * Expected failures are returned, not thrown (Next.js "Handling expected errors").
 * `code` is the API's error code, or "network_error" if the server cannot be reached.
 */
export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; code: string; status: number };

// Axios waits forever by default, which would leave the page loading. Retrying a timed
// out expense is safe: the form sends the same Idempotency-Key.
const REQUEST_TIMEOUT_MS = 10_000;

/** An axios client that resolves for every HTTP status, so callers get an ApiResult. */
export function createHttpClient(baseURL: string): AxiosInstance {
  return axios.create({ baseURL, timeout: REQUEST_TIMEOUT_MS, validateStatus: () => true });
}

/** Send a request and describe the outcome as an ApiResult instead of throwing. */
export async function send<T>(
  client: AxiosInstance,
  config: Parameters<AxiosInstance["request"]>[0],
): Promise<ApiResult<T>> {
  try {
    const response = await client.request(config);
    if (response.status >= 200 && response.status < 300) {
      return { ok: true, data: response.data as T };
    }
    return {
      ok: false,
      code: response.data?.error?.code ?? "unknown_error",
      status: response.status,
    };
  } catch {
    // No response in time: the server is down or too slow, or the URL is wrong.
    return { ok: false, code: "network_error", status: 502 };
  }
}
