// Money as whole satang (integers), never as floating-point baht.
//
// The largest amount, 9,999,999,999.99, is 999,999,999,999 satang: far below
// Number.MAX_SAFE_INTEGER, so integer arithmetic on numbers is exact. A balance would
// need about 9,000 such expenses to pass that limit. The rules mirror the backend
// (backend/app/validators/money.py and backend/app/services/splits.py), so the live
// preview matches what the API stores.

// Up to 10 integer digits and 2 decimal places: the range of NUMERIC(12,2).
const AMOUNT_PATTERN = /^(\d{1,10})(?:\.(\d{1,2}))?$/;
// What the API sends. No digit limit: a balance is a sum, so it can exceed NUMERIC(12,2).
const API_AMOUNT_PATTERN = /^-?(\d+)\.(\d{2})$/;

const thaiInteger = new Intl.NumberFormat("th-TH", { maximumFractionDigits: 0 });

export type Share = { member: string; satang: number };

/** Parse a typed amount such as "1000.00" or "10.5" into satang, or null. */
export function parseAmount(input: string): number | null {
  const match = AMOUNT_PATTERN.exec(input);
  if (match === null) {
    return null;
  }
  const baht = Number(match[1]);
  const satang = Number((match[2] ?? "").padEnd(2, "0"));
  return baht * 100 + satang;
}

/** Convert an amount from the API, such as "-333.33" for a balance, into satang. */
export function fromApiAmount(text: string): number {
  const match = API_AMOUNT_PATTERN.exec(text);
  if (match === null) {
    throw new Error(`Unexpected amount from the API: ${text}`);
  }
  const satang = Number(match[1]) * 100 + Number(match[2]);
  return text.startsWith("-") ? -satang : satang;
}

/** Format satang for display with Thai grouping, for example "1,000.00". */
export function formatAmount(satang: number): string {
  const sign = satang < 0 ? "-" : "";
  const absolute = Math.abs(satang);
  const baht = Math.floor(absolute / 100);
  const cents = String(absolute % 100).padStart(2, "0");
  return `${sign}${thaiInteger.format(baht)}.${cents}`;
}

/** Format satang the way the API expects: "1000.00", no grouping. */
export function toApiAmount(satang: number): string {
  const baht = Math.floor(satang / 100);
  const cents = String(satang % 100).padStart(2, "0");
  return `${baht}.${cents}`;
}

/**
 * Split equally. Remainder satang go one each to the first members, in the order
 * listed, exactly like allocate_equal in the backend.
 */
export function allocateEqual(totalSatang: number, members: string[]): Share[] {
  const base = Math.floor(totalSatang / members.length);
  const remainder = totalSatang % members.length;
  return members.map((member, index) => ({
    member,
    satang: base + (index < remainder ? 1 : 0),
  }));
}
