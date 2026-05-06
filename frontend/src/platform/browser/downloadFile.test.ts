import { afterEach, describe, expect, it, vi } from "vitest";

import { downloadFile } from "./downloadFile";

describe("downloadFile", () => {
  const originalCreateObjectURL = URL.createObjectURL;
  const originalRevokeObjectURL = URL.revokeObjectURL;

  afterEach(() => {
    URL.createObjectURL = originalCreateObjectURL;
    URL.revokeObjectURL = originalRevokeObjectURL;
    vi.restoreAllMocks();
  });

  it("creates an object URL, clicks an anchor, and revokes the URL", () => {
    const anchor = document.createElement("a");
    const clickSpy = vi.spyOn(anchor, "click").mockImplementation(() => {});
    const createElement = document.createElement.bind(document);
    const createElementSpy = vi.spyOn(document, "createElement").mockImplementation((tagName) => {
      return tagName === "a" ? anchor : createElement(tagName);
    });
    const createObjectURL = vi.fn(() => "blob:test-url");
    const revokeObjectURL = vi.fn();

    URL.createObjectURL = createObjectURL;
    URL.revokeObjectURL = revokeObjectURL;

    downloadFile("hello", "report.csv", "text/csv");

    expect(createElementSpy).toHaveBeenCalledWith("a");
    expect(anchor.href).toBe("blob:test-url");
    expect(anchor.download).toBe("report.csv");
    expect(clickSpy).toHaveBeenCalledOnce();
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:test-url");
  });
});
