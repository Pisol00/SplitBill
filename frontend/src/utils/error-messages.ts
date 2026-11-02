// Plain-language messages for API error codes (docs/api.md, "Errors").

const MESSAGES: Record<string, string> = {
  shares_mismatch: "The shares do not add up to the total.",
  member_not_in_group: "Everyone in the expense must be a member of this group.",
  group_not_found: "Not a member of this group.",
  not_payer: "Only the person who paid can delete this expense.",
  expense_not_found: "This expense no longer exists. It may already have been deleted.",
  idempotency_key_reused:
    "This expense was already submitted with different details. Please submit it again.",
  validation_error: "Some details are not valid. Please check the form.",
  missing_user: "Please choose a user.",
  unknown_user: "This user does not exist.",
  network_error: "Cannot reach the server. Please check that the API is running.",
};

const FALLBACK = "Something went wrong. Please try again.";

export function friendlyMessage(code: string): string {
  return MESSAGES[code] ?? FALLBACK;
}
