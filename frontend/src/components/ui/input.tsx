"use client";

import { type HTMLAttributes, useId } from "react";

import { Field, borderColor, fieldBorder } from "./field";

type Props = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  hideLabel?: boolean;
  placeholder?: string;
  error?: string | null;
  /** Text shown inside the box after the value, for example "THB". */
  suffix?: string;
  maxLength?: number;
  inputMode?: HTMLAttributes<HTMLInputElement>["inputMode"];
  align?: "left" | "right";
};

export function Input({
  label,
  value,
  onChange,
  hideLabel = false,
  placeholder,
  error,
  suffix,
  maxLength,
  inputMode,
  align = "left",
}: Props) {
  const id = useId();
  const invalid = Boolean(error);

  return (
    <Field id={id} label={label} hideLabel={hideLabel} error={error}>
      <div className={`flex items-center ${fieldBorder} ${borderColor(invalid)}`}>
        <input
          id={id}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
          maxLength={maxLength}
          inputMode={inputMode}
          aria-invalid={invalid}
          aria-describedby={invalid ? `${id}-error` : undefined}
          className={`h-10 w-full min-w-0 rounded-md bg-transparent px-3 text-sm text-fg placeholder:text-fg-subtle focus:outline-none ${
            align === "right" ? "text-right tabular-nums" : ""
          }`}
        />
        {suffix && (
          <span aria-hidden="true" className="pr-3 text-xs font-medium text-fg-subtle">
            {suffix}
          </span>
        )}
      </div>
    </Field>
  );
}
