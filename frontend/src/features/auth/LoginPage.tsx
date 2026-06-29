import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "./AuthContext";
import { Button } from "../../shared/ui/UI";

type Mode = "signin" | "signup";

const DEMO_EMAIL = "catiya3171@justnapa.com";
const DEMO_PASSWORD = "demo123";

export function LoginPage() {
  const { signIn, signUp, configError } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState<Mode>("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [signedUp, setSignedUp] = useState(false);

  const handleDemoLogin = async () => {
    setMode("signin");
    setError(null);
    setEmail(DEMO_EMAIL);
    setPassword(DEMO_PASSWORD);
    setLoading(true);
    try {
      await signIn(DEMO_EMAIL, DEMO_PASSWORD);
      navigate("/");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "An error occurred";
      if (message.includes("Failed to fetch")) {
        setError("無法連線到 Supabase。請確認 frontend/.env 的 Supabase URL / Publishable Key 是否正確，並重新啟動前端。");
      } else {
        setError(message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === "signin") {
        await signIn(email, password);
        navigate("/");
      } else {
        await signUp(email, password);
        setSignedUp(true);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "An error occurred";
      if (message.includes("Failed to fetch")) {
        setError("無法連線到 Supabase。請確認 frontend/.env 的 Supabase URL / Publishable Key 是否正確，並重新啟動前端。");
      } else {
        setError(message);
      }
    } finally {
      setLoading(false);
    }
  };

  if (signedUp) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-paper px-4">
        <div className="w-full max-w-sm rounded-3xl border border-line bg-white p-8 text-center shadow-card">
          <h2 className="text-xl font-bold text-ink">確認信已寄出</h2>
          <p className="mt-2 text-sm text-muted">請查收 {email} 的確認信後再登入。</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-paper px-4">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(15,118,110,0.16),transparent_24rem),radial-gradient(circle_at_85%_15%,rgba(180,132,66,0.14),transparent_20rem)]" />
      <div className="relative w-full max-w-sm rounded-[2rem] border border-line/80 bg-panel/95 p-8 shadow-card backdrop-blur">
        <p className="text-xs font-bold uppercase tracking-[0.24em] text-accent">Portfolio Access</p>
        <h1 className="mt-3 text-3xl font-black tracking-tight text-ink">Stocker</h1>
        <p className="mt-2 text-sm leading-6 text-muted">登入後即可使用你的個人投資資料與設定。</p>

        <div className="mt-6 flex gap-3 border-b border-line/80">
          {(["signin", "signup"] as const).map((item) => (
            <button
              key={item}
              type="button"
              className={`pb-2 text-sm font-semibold transition ${
                mode === item ? "border-b-2 border-accent text-accent" : "text-muted hover:text-ink"
              }`}
              onClick={() => {
                setMode(item);
                setError(null);
              }}
            >
              {item === "signin" ? "登入" : "註冊"}
            </button>
          ))}
        </div>

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          {configError ? <p className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{configError}</p> : null}
          <label className="block">
            <span className="text-sm font-medium text-ink">Email</span>
            <input
              type="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="mt-1.5 w-full rounded-xl border border-line bg-white/90 px-3 py-2.5 text-sm text-ink outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/15"
            />
          </label>
          <label className="block">
            <span className="text-sm font-medium text-ink">密碼</span>
            <input
              type="password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-1.5 w-full rounded-xl border border-line bg-white/90 px-3 py-2.5 text-sm text-ink outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/15"
            />
          </label>
          {error ? <p className="text-sm text-rose-600">{error}</p> : null}
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-accent px-4 py-2.5 text-sm font-semibold text-white shadow-soft transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "處理中..." : mode === "signin" ? "登入" : "註冊"}
          </button>
          {mode === "signin" ? (
            <Button type="button" tone="secondary" className="w-full" onClick={handleDemoLogin} disabled={loading}>
              搶先體驗 (免註冊)
            </Button>
          ) : null}
        </form>
      </div>
    </div>
  );
}
