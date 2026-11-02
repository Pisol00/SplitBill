"use client";

import { useId } from "react";

import { Field, borderColor, fieldBorder } from "./field";

type Props = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  error?: string | null;
  /** Also shows a "12 / 255" counter. */
  maxLength?: number;
  rows?: number;
};

export function TextArea({
  label,
  value,
  onChange,
  placeholder,
  error,
  maxLength,
  rows = 2,
}: Props) {
  const id = useId();
  const invalid = Boolean(error);

  return (
    <Field
      id={id}
      label={label}
      error={error}
      hint={maxLength ? `${value.length} / ${maxLength}` : undefined}
    >
      <div className={`${fieldBorder} ${borderColor(invalid)}`}>
        <textarea
          id={id}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
          maxLength={maxLength}
          rows={rows}
          aria-invalid={invalid}
          aria-describedby={invalid ? `${id}-error` : undefined}
          className="block w-full resize-y rounded-md bg-transparent px-3 py-2 text-sm text-fg placeholder:text-fg-subtle focus:outline-none"
        />
      </div>
    </Field>
  );
}
