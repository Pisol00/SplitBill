// Keyboard movement in a list of options, kept apart from the component so it can
// be unit-tested. Follows the WAI-ARIA select-only combobox pattern.

/** The option to highlight after a key press, or null if the key does not move it. */
export function nextActiveIndex(
  current: number,
  key: string,
  count: number,
): number | null {
  switch (key) {
    case "ArrowDown":
      return Math.min(current + 1, count - 1);
    case "ArrowUp":
      return Math.max(current - 1, 0);
    case "Home":
      return 0;
    case "End":
      return count - 1;
    default:
      return null;
  }
}

/**
 * The option to select after a key press in a radio group, or null. Unlike a
 * listbox, arrow keys wrap around (WAI-ARIA radio group pattern).
 */
export function nextRadioIndex(
  current: number,
  key: string,
  count: number,
): number | null {
  switch (key) {
    case "ArrowRight":
    case "ArrowDown":
      return (current + 1) % count;
    case "ArrowLeft":
    case "ArrowUp":
      return (current - 1 + count) % count;
    case "Home":
      return 0;
    case "End":
      return count - 1;
    default:
      return null;
  }
}
