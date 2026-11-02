import type { ReactNode } from "react";

// Shared label, hint and error layout for Input and TextArea.

export const fieldBorder =
  "rounded-md border bg-surface shadow-xs transition-colors duration-150 ease-standard focus-within:ring-2 focus-within:ring-offset-0";

export function borderColor(invalid: boolean): string {
  return invalid
    ? "border-danger focus-within:ring-danger"
    : "border-line hover:border-line-strong focus-within:border-ring focus-within:ring-ring";
}

type FieldProps = {
  id: string;
  label: string;
  hideLabel?: boolean;
  hint?: ReactNode;
  error?: string | null;
  children: ReactNode;
};

export function Field({ id, label, hideLabel, hint, error, children }: FieldProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label
        htmlFor={id}
        // sr-only keeps the label for screen readers when it is not shown.
        className={hideLabel ? "sr-only" : "text-sm font-medium text-fg"}
      >
        {label}
      </label>
      {children}
      {(error || hint) && (
        <div className="flex justify-between gap-3 text-xs">
          {error ? (
            <span id={`${id}-error`} className="text-danger">
              {error}
            </span>
          ) : (
            <span />
          )}
          {hint && <span className="text-fg-subtle tabular-nums">{hint}</span>}
        </div>
      )}
    </div>
  );
}
