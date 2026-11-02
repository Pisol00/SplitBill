import assert from "node:assert/strict";
import { test } from "node:test";

import { friendlyMessage } from "../utils/error-messages.ts";

test("API error codes become plain-language messages from the brief", () => {
  assert.equal(friendlyMessage("shares_mismatch"), "The shares do not add up to the total.");
  assert.equal(friendlyMessage("group_not_found"), "Not a member of this group.");
});

test("unknown codes get a general message", () => {
  assert.equal(friendlyMessage("something_new"), "Something went wrong. Please try again.");
});
