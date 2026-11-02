import assert from "node:assert/strict";
import { test } from "node:test";

import { nextActiveIndex, nextRadioIndex } from "../components/ui/listbox.ts";

test("arrow keys move one option and stop at the ends", () => {
  assert.equal(nextActiveIndex(0, "ArrowDown", 3), 1);
  assert.equal(nextActiveIndex(2, "ArrowDown", 3), 2);
  assert.equal(nextActiveIndex(2, "ArrowUp", 3), 1);
  assert.equal(nextActiveIndex(0, "ArrowUp", 3), 0);
});

test("Home and End jump to the first and last option", () => {
  assert.equal(nextActiveIndex(1, "Home", 4), 0);
  assert.equal(nextActiveIndex(1, "End", 4), 3);
});

test("other keys do not move the active option", () => {
  assert.equal(nextActiveIndex(1, "a", 3), null);
  assert.equal(nextActiveIndex(1, "Enter", 3), null);
});

test("radio groups wrap around in both directions", () => {
  assert.equal(nextRadioIndex(1, "ArrowRight", 2), 0);
  assert.equal(nextRadioIndex(0, "ArrowLeft", 2), 1);
  assert.equal(nextRadioIndex(0, "ArrowDown", 3), 1);
  assert.equal(nextRadioIndex(0, "ArrowUp", 3), 2);
  assert.equal(nextRadioIndex(1, "Home", 3), 0);
  assert.equal(nextRadioIndex(1, "End", 3), 2);
  assert.equal(nextRadioIndex(1, "Enter", 3), null);
});
