// Run with: npm test (node:test, no extra dependencies).
import assert from "node:assert/strict";
import { createServer } from "node:http";
import type { AddressInfo } from "node:net";
import { test } from "node:test";

import { createHttpClient, send } from "../utils/http.ts";

test("every client gives up on a server that does not answer", () => {
  assert.ok((createHttpClient("/api").defaults.timeout ?? 0) > 0);
});

test("a server that accepts the request but never answers is a network error", async (t) => {
  const silent = createServer(() => {});
  await new Promise<void>((resolve) => silent.listen(0, "127.0.0.1", resolve));
  t.after(() => {
    silent.closeAllConnections();
    silent.close();
  });
  const { port } = silent.address() as AddressInfo;
  const client = createHttpClient(`http://127.0.0.1:${port}`);

  const result = await send(client, { url: "/groups", timeout: 50 });

  assert.deepEqual(result, { ok: false, code: "network_error", status: 502 });
});
