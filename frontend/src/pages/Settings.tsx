import { Download, KeyRound, LogOut, SlidersHorizontal, Upload } from "lucide-react";
import { useEffect, useRef, useState, type ChangeEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { api } from "../api/client";
import { portfolioQueryKeys, queryKeys, useInvalidateQueries } from "../api/query";
import { useAuth } from "../contexts/AuthContext";
import { Button, Card, PageHeader, SkeletonBlock } from "../components/shared/UI";
import { percent } from "../components/shared/format";
import { useAdminCapabilities, useSettings } from "../hooks/queries";

export function Settings() {
  const { data, isLoading } = useSettings();
  const adminCapabilities = useAdminCapabilities();
  const { signOut, updatePassword } = useAuth();
  const [rate, setRate] = useState(0);
  const [exporting, setExporting] = useState(false);
  const [importMessage, setImportMessage] = useState<string | null>(null);
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const invalidateQueries = useInvalidateQueries();
  const mutation = useMutation({
    mutationFn: async (commission_discount_rate: number) =>
      api.put("/settings", { commission_discount_rate }),
    onSuccess: () => invalidateQueries([queryKeys.settings])
  });
  const importMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return (await api.post("/export/import", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      })).data as {
        transactions_imported: number;
        cashflows_imported: number;
      };
    },
    onSuccess: async (result) => {
      setImportMessage(`已匯入 ${result.transactions_imported} 筆交易、${result.cashflows_imported} 筆出入金。`);
      await invalidateQueries([queryKeys.settings, ...portfolioQueryKeys]);
      if (fileInputRef.current) fileInputRef.current.value = "";
    },
    onError: () => {
      setImportMessage("匯入失敗，請確認檔案格式是否為系統匯出的 Excel。");
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  });
  const passwordMutation = useMutation({
    mutationFn: async ({ currentPassword, newPassword }: { currentPassword: string; newPassword: string }) => {
      await updatePassword(currentPassword, newPassword);
    },
    onSuccess: () => {
      setPasswordMessage("密碼已更新。");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    },
    onError: (error: unknown) => {
      setPasswordMessage(error instanceof Error ? error.message : "密碼更新失敗。");
    }
  });

  useEffect(() => {
    if (data) setRate(data.commission_discount_rate);
  }, [data]);

  const handleExport = async () => {
    setExporting(true);
    try {
      const response = await api.get("/export", { responseType: "blob" });
      const url = URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.download = "stocker_export.xlsx";
      link.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  };

  const handleImportSelect = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setImportMessage(null);
    importMutation.mutate(file);
  };

  const handlePasswordSubmit = () => {
    setPasswordMessage(null);
    if (!currentPassword) {
      setPasswordMessage("請輸入目前密碼。");
      return;
    }
    if (newPassword.length < 6) {
      setPasswordMessage("新密碼至少需要 6 個字元。");
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordMessage("兩次輸入的密碼不一致。");
      return;
    }
    passwordMutation.mutate({ currentPassword, newPassword });
  };

  if (isLoading) return <SkeletonBlock label="載入設定中..." />;

  return (
    <section className="max-w-3xl space-y-5">
      <PageHeader
        eyebrow="Preferences"
        title="設定"
        description="調整會影響後續交易計算的全域設定。"
        action={adminCapabilities.data?.is_admin ? (
          <Link to="/admin" aria-label="Open Admin">
            <Button tone="secondary">Open Admin</Button>
          </Link>
        ) : null}
      />

      <Card>
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-start gap-3">
            <span className="rounded-2xl bg-teal-50 p-3 text-accent">
              <SlidersHorizontal className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <h2 className="text-lg font-bold text-ink">手續費折數</h2>
              <p className="mt-1 text-sm leading-6 text-muted">
                目前 {percent(rate)}。儲存後，新交易與費用預估會使用這個折扣。
              </p>
            </div>
          </div>
          <div className="rounded-2xl border border-line bg-white/75 px-4 py-3 text-2xl font-bold text-accent">
            {percent(rate)}
          </div>
        </div>

        <input
          className="mt-6 w-full accent-teal-700"
          type="range"
          min="0"
          max="1"
          step="0.01"
          value={rate}
          onChange={(event) => setRate(Number(event.target.value))}
        />
        <div className="mt-3 flex justify-between text-xs font-semibold text-muted">
          <span>0%</span>
          <span>50%</span>
          <span>100%</span>
        </div>
        <div className="mt-5 flex justify-end">
          <Button disabled={mutation.isPending} onClick={() => mutation.mutate(rate)}>
            儲存
          </Button>
        </div>
      </Card>

      <Card>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-3">
            <span className="rounded-2xl bg-teal-50 p-3 text-accent">
              <Download className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <h2 className="text-lg font-bold text-ink">匯出資料</h2>
              <p className="mt-1 text-sm text-muted">下載包含交易紀錄與出入金的 Excel 檔案。</p>
            </div>
          </div>
          <Button disabled={exporting} onClick={handleExport}>
            {exporting ? "匯出中..." : "匯出 Excel"}
          </Button>
        </div>
      </Card>

      <Card>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-3">
            <span className="rounded-2xl bg-amber-50 p-3 text-amber-700">
              <Upload className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <h2 className="text-lg font-bold text-ink">匯入資料</h2>
              <p className="mt-1 text-sm text-muted">上傳系統匯出的 Excel，將覆蓋目前帳號的交易紀錄與出入金資料。</p>
              {importMessage ? <p className="mt-2 text-sm font-medium text-accent">{importMessage}</p> : null}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx"
              className="hidden"
              onChange={(event) => void handleImportSelect(event)}
            />
            <Button
              disabled={importMutation.isPending}
              onClick={() => fileInputRef.current?.click()}
            >
              {importMutation.isPending ? "匯入中..." : "選擇 Excel"}
            </Button>
          </div>
        </div>
      </Card>

      <Card>
        <div className="flex items-start gap-3">
          <span className="rounded-2xl bg-sky-50 p-3 text-sky-700">
            <KeyRound className="h-5 w-5" aria-hidden="true" />
          </span>
          <div className="min-w-0 flex-1">
            <h2 className="text-lg font-bold text-ink">更改密碼</h2>
            <p className="mt-1 text-sm text-muted">更新目前帳號的登入密碼。</p>
            {passwordMessage ? <p className="mt-2 text-sm font-medium text-accent">{passwordMessage}</p> : null}
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <label className="block sm:col-span-2">
                <span className="text-sm font-medium text-ink">目前密碼</span>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(event) => setCurrentPassword(event.target.value)}
                  className="mt-1.5 w-full rounded-xl border border-line bg-white/90 px-3 py-2.5 text-sm text-ink outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/15"
                />
              </label>
              <label className="block">
                <span className="text-sm font-medium text-ink">新密碼</span>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                  className="mt-1.5 w-full rounded-xl border border-line bg-white/90 px-3 py-2.5 text-sm text-ink outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/15"
                />
              </label>
              <label className="block">
                <span className="text-sm font-medium text-ink">確認新密碼</span>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  className="mt-1.5 w-full rounded-xl border border-line bg-white/90 px-3 py-2.5 text-sm text-ink outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/15"
                />
              </label>
            </div>
            <div className="mt-4 flex justify-end">
              <Button disabled={passwordMutation.isPending} onClick={handlePasswordSubmit}>
                {passwordMutation.isPending ? "更新中..." : "更新密碼"}
              </Button>
            </div>
          </div>
        </div>
      </Card>

      <Card>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-3">
            <span className="rounded-2xl bg-rose-50 p-3 text-rose-500">
              <LogOut className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <h2 className="text-lg font-bold text-ink">登出</h2>
              <p className="mt-1 text-sm text-muted">結束目前的登入工作階段。</p>
            </div>
          </div>
          <Button tone="secondary" onClick={() => void signOut()}>
            登出
          </Button>
        </div>
      </Card>
    </section>
  );
}
