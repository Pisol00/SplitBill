"use client";

import { type KeyboardEvent, useId, useRef } from "react";

import { nextRadioIndex } from "./listbox";

// A radio group drawn as joined buttons, following the WAI-ARIA radio group pattern:
// one tab stop, arrow keys move and select. https://www.w3.org/WAI/ARIA/apg/patterns/radio/

type Option<T extends string> = { value: T; label: string };

type Props<T extends string> = {
  label: string;
  value: T;
  options: Option<T>[];
  onChange: (value: T) => void;
};

export function SegmentedControl<T extends string>({
  label,
  value,
  options,
  onChange,
}: Props<T>) {
  const labelId = useId();
  const buttons = useRef<(HTMLButtonElement | null)[]>([]);
  const selectedIndex = options.findIndex((option) => option.value === value);

  function handleKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    const next = nextRadioIndex(selectedIndex, event.key, options.length);
    if (next === null) return;
    event.preventDefault();
    onChange(options[next].value);
    buttons.current[next]?.focus();
  }

  return (
    <div className="flex flex-col gap-1.5">
      <span id={labelId} className="text-sm font-medium text-fg">
        {label}
      </span>
      <div
        role="radiogroup"
        aria-labelledby={labelId}
        className="inline-flex rounded-md bg-surface-muted p-1"
      >
        {options.map((option, index) => {
          const checked = index === selectedIndex;
          return (
            <button
              key={option.value}
              ref={(element) => {
                buttons.current[index] = element;
              }}
              type="button"
              role="radio"
              aria-checked={checked}
              tabIndex={checked ? 0 : -1}
              onClick={() => onChange(option.value)}
              onKeyDown={handleKeyDown}
              className={`h-8 flex-1 rounded-sm px-3 text-sm font-medium transition-colors duration-150 ease-standard focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                checked
                  ? "bg-surface text-fg shadow-xs"
                  : "text-fg-muted hover:text-fg"
              }`}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
