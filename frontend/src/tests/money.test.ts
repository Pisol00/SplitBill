// Money arithmetic must match the backend exactly (backend/tests/test_splits.py).
// Run with: npm test (node:test, no extra dependencies).
import assert from "node:assert/strict";
import { test } from "node:test";

import {
  allocateEqual,
  formatAmount,
  fromApiAmount,
  parseAmount,
  toApiAmount,
} from "../utils/money.ts";

test("100.00 split three ways gives 33.34, 33.33, 33.33 like the backend", () => {
  const shares = allocateEqual(10000, ["alice", "bob", "carol"]);

  assert.deepEqual(
    shares.map(({ member, satang }) => [member, formatAmount(satang)]),
    [
      ["alice", "33.34"],
      ["bob", "33.33"],
      ["carol", "33.33"],
    ],
  );
});

test("remainder satang go to members in the order listed", () => {
  const shares = allocateEqual(10000, ["carol", "alice", "bob"]);

  assert.deepEqual(
    shares.map(({ satang }) => satang),
    [3334, 3333, 3333],
  );
  assert.equal(shares[0].member, "carol");
});

test("one satang among three gives 0.01, 0.00, 0.00", () => {
  const shares = allocateEqual(1, ["alice", "bob", "carol"]);

  assert.deepEqual(
    shares.map(({ satang }) => satang),
    [1, 0, 0],
  );
});

test("equal shares always sum to the amount", () => {
  for (const total of [1, 2, 100, 999, 10000, 100001, 999999999999]) {
    for (let count = 1; count <= 7; count++) {
      const members = Array.from({ length: count }, (_, i) => `m${i}`);
      const sum = allocateEqual(total, members).reduce((s, x) => s + x.satang, 0);
      assert.equal(sum, total, `${total} among ${count}`);
    }
  }
});

test("0.1 + 0.2 displays 0.30 (no floating-point error)", () => {
  const total = parseAmount("0.1")! + parseAmount("0.2")!;

  assert.equal(formatAmount(total), "0.30");
});

test("amounts use Thai formatting with two decimal places", () => {
  assert.equal(formatAmount(100000), "1,000.00");
  assert.equal(formatAmount(0), "0.00");
  assert.equal(formatAmount(999999999999), "9,999,999,999.99");
  assert.equal(formatAmount(-33333), "-333.33");
});

test("parseAmount accepts what the backend accepts", () => {
  assert.equal(parseAmount("1000.00"), 100000);
  assert.equal(parseAmount("10.5"), 1050);
  assert.equal(parseAmount("10"), 1000);
  assert.equal(parseAmount("0.01"), 1);
  assert.equal(parseAmount("9999999999.99"), 999999999999);
});

test("parseAmount rejects what the backend rejects", () => {
  for (const input of ["", " 10", "10.005", "1e3", "-5", "10.", ".5", "1,000", "abc", "10000000000"]) {
    assert.equal(parseAmount(input), null, JSON.stringify(input));
  }
});

test("amounts are sent to the API as plain strings with two decimals", () => {
  assert.equal(toApiAmount(1050), "10.50");
  assert.equal(toApiAmount(100000), "1000.00");
  assert.equal(toApiAmount(1), "0.01");
});

test("amounts from the API, including negative balances, become satang", () => {
  assert.equal(fromApiAmount("1000.00"), 100000);
  assert.equal(fromApiAmount("-333.33"), -33333);
  assert.equal(fromApiAmount("0.00"), 0);
  assert.equal(formatAmount(fromApiAmount("-1000.00")), "-1,000.00");
});

test("a balance can exceed the largest single amount, because it is a sum", () => {
  assert.equal(fromApiAmount("19999999999.98"), 1999999999998);
  assert.equal(fromApiAmount("-19999999999.98"), -1999999999998);
  assert.equal(formatAmount(fromApiAmount("19999999999.98")), "19,999,999,999.98");
});

test("an amount from the API that is not money is still rejected", () => {
  for (const text of ["", "abc", "1.5.5", "--1.00", "10.005"]) {
    assert.throws(() => fromApiAmount(text), /Unexpected amount/, text);
  }
});

test("a typed amount is still limited to 10 integer digits", () => {
  assert.equal(parseAmount("19999999999.98"), null);
});
