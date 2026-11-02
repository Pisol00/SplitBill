// Turns an ApiResult into a Route Handler response, keeping the API's status and its
// {"error": {"code": ...}} body, so the browser sees the same contract as the API.
import "server-only";

import type { ApiResult } from "@/utils/http";

export function respond<T>(result: ApiResult<T>): Response {
  if (result.ok) {
    return Response.json(result.data);
  }
  return Response.json({ error: { code: result.code } }, { status: result.status });
}

/** The requesting user, forwarded from the browser as the X-User header. */
export function requestingUser(request: Request): string {
  return request.headers.get("X-User") ?? "";
}
