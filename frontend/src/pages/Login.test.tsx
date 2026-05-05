import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { Login } from "./Login";

const navigateMock = vi.fn();
const signInMock = vi.fn().mockResolvedValue(undefined);
const signUpMock = vi.fn();

vi.mock("react-router-dom", () => ({
  useNavigate: () => navigateMock,
}));

vi.mock("../contexts/AuthContext", () => ({
  useAuth: () => ({
    signIn: signInMock,
    signUp: signUpMock,
    configError: null,
  }),
}));

describe("Login", () => {
  it("logs in with the demo account when the demo button is clicked", async () => {
    const user = userEvent.setup();

    render(<Login />);

    await user.click(screen.getByRole("button", { name: "Try with Demo Account" }));

    expect(signInMock).toHaveBeenCalledWith("catiya3171@justnapa.com", "demo123");
    expect(navigateMock).toHaveBeenCalledWith("/");
    expect(screen.getByLabelText("Email")).toHaveValue("catiya3171@justnapa.com");
    expect(screen.getByLabelText("密碼")).toHaveValue("demo123");
  });
});
