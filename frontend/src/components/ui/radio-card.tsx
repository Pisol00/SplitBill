import { Check } from "lucide-react";

import { Avatar } from "./avatar";

type Props = {
  name: string;
  label: string;
  checked: boolean;
  onChange: () => void;
};

// A native radio drawn as a card, so keyboard and screen readers work as usual.
export function RadioCard({ name, label, checked, onChange }: Props) {
  return (
    <label
      className={`relative flex min-w-0 cursor-pointer flex-col items-center gap-2 rounded-md border px-2 py-4 text-sm text-fg transition-colors duration-150 ease-standard has-focus-visible:ring-2 has-focus-visible:ring-ring ${
        checked
          ? "border-accent bg-surface font-medium ring-1 ring-accent"
          : "border-line bg-surface hover:border-line-strong hover:bg-surface-hover"
      }`}
    >
      <input
        type="radio"
        name={name}
        checked={checked}
        onChange={onChange}
        className="sr-only"
      />
      {checked && (
        <Check className="absolute top-1.5 right-1.5 h-4.5 w-4.5 rounded-full bg-accent p-0.5 text-primary-fg" />
      )}
      <Avatar name={label} size="lg" />
      <span className="w-full text-center break-words">{label}</span>
    </label>
  );
}
