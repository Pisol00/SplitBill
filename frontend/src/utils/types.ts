// API shapes, shared by Server and Client Components. They follow docs/api.md.

export type GroupSummary = { id: number; name: string };
export type GroupDetail = { id: number; name: string; members: string[] };
export type Share = { member: string; amount: string };
export type Expense = {
  id: number;
  group_id: number;
  description: string;
  paid_by: string;
  amount: string;
  split_type: "equal" | "exact";
  shares: Share[];
  created_at: string;
};
export type Balance = { member: string; balance: string };
export type Payment = {
  id: number;
  expense_id: number;
  from_member: string;
  to_member: string;
  amount: string;
  status: "pending" | "confirmed" | "rejected";
  created_at: string;
  decided_at: string | null;
};

export type NewExpense = {
  description: string;
  paid_by: string;
  amount: string;
  split:
    | { type: "equal"; members: string[] }
    | { type: "exact"; shares: Record<string, string> };
};
