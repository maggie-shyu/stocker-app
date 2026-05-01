import { describe, expect, it } from "vitest";

import { money, percent, signedClass } from "./format";

describe("format helpers", () => {
  it("formats money and percentages for display", () => {
    expect(money(1234.4)).toBe("1,234");
    expect(money(null)).toBe("0");
    expect(percent(0.1234)).toBe("12.34%");
    expect(percent(undefined)).toBe("0.00%");
  });

  it("returns semantic classes for signed values", () => {
    expect(signedClass(1)).toBe("text-gain");
    expect(signedClass(-1)).toBe("text-loss");
    expect(signedClass(0)).toBe("text-muted");
    expect(signedClass(null)).toBe("text-muted");
  });
});
