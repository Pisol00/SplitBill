import type { ReactNode } from "react";

import { Check } from "lucide-react";

type Props = {
  checked: boolean;
  onChange: (checked: boolean) => void;
  children: ReactNode;
};

// A native checkbox, so keyboard and screen readers work as usual, drawn with tokens.
export function Checkbox({ checked, onChange, children }: Props) {
  return (
    <label className="group flex flex-1 cursor-pointer items-center gap-2.5 self-stretch text-sm text-fg">
      <span className="relative inline-flex h-4.5 w-4.5 shrink-0">
        <input
          type="checkbox"
          checked={checked}
          onChange={(event) => onChange(event.target.checked)}
          className="peer h-4.5 w-4.5 cursor-pointer appearance-none rounded-sm border border-line-strong bg-surface transition-colors duration-150 ease-standard checked:border-primary checked:bg-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-surface"
        />
        <Check className="pointer-events-none absolute inset-0 h-4.5 w-4.5 p-0.5 text-primary-fg opacity-0 peer-checked:opacity-100" />
      </span>
      {children}
    </label>
  );
}
