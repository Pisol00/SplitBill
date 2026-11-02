"use client";

import { Check, ChevronDown } from "lucide-react";
import { type KeyboardEvent, useEffect, useId, useRef, useState } from "react";

import { nextActiveIndex } from "./listbox";

// A dropdown built without a UI library, following the WAI-ARIA select-only
// combobox pattern: https://www.w3.org/WAI/ARIA/apg/patterns/combobox/

export type SelectOption = { value: string; label: string };

type Props = {
  label: string;
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
};

export function Select({
  label,
  value,
  options,
  onChange,
  disabled = false,
  placeholder = "Select...",
}: Props) {
  const id = useId();
  const labelId = `${id}-label`;
  const listId = `${id}-list`;
  const optionId = (index: number) => `${id}-option-${index}`;

  const [open, setOpen] = useState(false);
  // The highlighted option while the list is open.
  const [active, setActive] = useState(0);
  const root = useRef<HTMLDivElement>(null);

  const selectedIndex = options.findIndex((option) => option.value === value);
  const selected = options[selectedIndex];
  const isDisabled = disabled || options.length === 0;

  // Close when the user clicks anywhere outside the dropdown.
  useEffect(() => {
    if (!open) return;
    function closeOnOutsideClick(event: PointerEvent) {
      if (!root.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("pointerdown", closeOnOutsideClick);
    return () => document.removeEventListener("pointerdown", closeOnOutsideClick);
  }, [open]);

  // Keep the highlighted option visible in a long list.
  useEffect(() => {
    if (open) {
      document.getElementById(optionId(active))?.scrollIntoView({ block: "nearest" });
    }
  });

  function openList() {
    setActive(Math.max(selectedIndex, 0));
    setOpen(true);
  }

  function choose(index: number) {
    const option = options[index];
    if (option) {
      onChange(option.value);
    }
    setOpen(false);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    if (isDisabled) return;

    if (!open) {
      if (["ArrowDown", "ArrowUp", "Enter", " "].includes(event.key)) {
        event.preventDefault();
        openList();
      }
      return;
    }

    switch (event.key) {
      case "Enter":
      case " ":
        event.preventDefault();
        choose(active);
        return;
      case "Escape":
        event.preventDefault();
        setOpen(false);
        return;
      case "Tab":
        setOpen(false);
        return;
    }

    const next = nextActiveIndex(active, event.key, options.length);
    if (next !== null) {
      event.preventDefault();
      setActive(next);
    }
  }

  return (
    <div ref={root} className="relative flex min-w-0 flex-col gap-1.5 sm:min-w-44">
      <span id={labelId} className="text-sm font-medium text-fg">
        {label}
      </span>

      <button
        type="button"
        role="combobox"
        aria-labelledby={labelId}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listId}
        aria-activedescendant={open ? optionId(active) : undefined}
        disabled={isDisabled}
        onClick={() => (open ? setOpen(false) : openList())}
        onKeyDown={handleKeyDown}
        className="flex h-10 items-center justify-between gap-3 rounded-md border border-line bg-surface px-3 text-left text-sm text-fg shadow-xs transition-colors duration-150 ease-standard hover:border-line-strong focus:outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:bg-surface-muted disabled:text-fg-subtle"
      >
        <span className={`truncate ${selected ? "" : "text-fg-subtle"}`}>
          {selected?.label ?? placeholder}
        </span>
        <ChevronDown
          className={`h-4 w-4 shrink-0 text-fg-subtle transition-transform duration-150 ease-standard ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <ul
          id={listId}
          role="listbox"
          aria-labelledby={labelId}
          className="absolute top-full z-20 mt-1.5 max-h-60 w-full overflow-auto rounded-md border border-line bg-surface p-1 shadow-lg"
        >
          {options.map((option, index) => {
            const isSelected = index === selectedIndex;
            return (
              <li
                key={option.value}
                id={optionId(index)}
                role="option"
                aria-selected={isSelected}
                // Keep focus on the button, so the keyboard keeps working.
                onMouseDown={(event) => event.preventDefault()}
                onMouseEnter={() => setActive(index)}
                onClick={() => choose(index)}
                className={`flex cursor-pointer items-center justify-between gap-3 rounded-sm px-2.5 py-2 text-sm text-fg ${
                  index === active ? "bg-surface-hover" : ""
                } ${isSelected ? "font-medium" : ""}`}
              >
                {option.label}
                {isSelected && <Check className="h-4 w-4 text-accent" />}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
