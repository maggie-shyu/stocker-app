import { describe, expect, it } from "vitest";

import { money, percent, price, shares, signedClass } from "./format";

describe("format helpers", () => {
  it("formats money and percentages for display", () => {
    expect(money(1234.4)).toBe("1,234");
    expect(money(null)).toBe("0");
    expect(shares(1234567)).toBe("1,234,567");
    expect(shares(1234.5)).toBe("1,234.5");
    expect(price(1234)).toBe("1,234");
    expect(price(1234.5)).toBe("1,234.5");
    expect(price(1234.56)).toBe("1,234.56");
    expect(price(1234.567)).toBe("1,234.57");
    expect(percent(0.1234)).toBe("+12.34%");
    expect(percent(undefined)).toBe("+0.00%");
  });

  it("returns semantic classes for signed values", () => {
    expect(signedClass(1)).toBe("text-gain");
    expect(signedClass(-1)).toBe("text-loss");
    expect(signedClass(0)).toBe("text-muted");
    expect(signedClass(null)).toBe("text-muted");
  });
});
