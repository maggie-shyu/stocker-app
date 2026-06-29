import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { LoginPage } from "./LoginPage";

const navigateMock = vi.fn();
const signInMock = vi.fn().mockResolvedValue(undefined);
const signUpMock = vi.fn();

vi.mock("react-router-dom", () => ({
  useNavigate: () => navigateMock,
}));

vi.mock("./AuthContext", () => ({
  useAuth: () => ({
    signIn: signInMock,
    signUp: signUpMock,
    configError: null,
  }),
}));

describe("LoginPage", () => {
  it("logs in with the demo account when the demo button is clicked", async () => {
    const user = userEvent.setup();

    render(<LoginPage />);

    await user.click(screen.getByRole("button", { name: "搶先體驗 (免註冊)" }));

    expect(signInMock).toHaveBeenCalledWith("catiya3171@justnapa.com", "demo123");
    expect(navigateMock).toHaveBeenCalledWith("/");
    expect(screen.getByLabelText("Email")).toHaveValue("catiya3171@justnapa.com");
    expect(screen.getByLabelText("密碼")).toHaveValue("demo123");
  });
});
