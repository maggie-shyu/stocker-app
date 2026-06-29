import { Download, KeyRound, LogOut, Receipt, SlidersHorizontal, Upload, X } from "lucide-react";
import { useEffect, useRef, useState, type ChangeEvent, type ReactNode } from "react";
import { useMutation } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import type { UserSettings } from "./types";
import { api } from "../../platform/api/client";
import { portfolioQueryKeys, queryKeys, useInvalidateQueries } from "../../platform/api/query";
import { downloadFile } from "../../platform/browser/downloadFile";
import { percent } from "../../shared/lib/format";
import { Button, Card, Field, PageHeader, SkeletonBlock } from "../../shared/ui/UI";
import { useAdminCapabilities } from "../admin/queries";
import { useAuth } from "../auth/AuthContext";
import { useCashflows, useTransactions } from "../ledger/queries";
import { useSettings } from "./queries";

function DialogShell({
  open,
  title,
  description,
  onClose,
  children,
  footer,
}: {
  open: boolean;
  title: string;
  description: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
}) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        aria-label="關閉視窗"
        className="absolute inset-0 bg-paper/90"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        className="relative w-full max-w-lg rounded-[2rem] border border-line/80 bg-panel/95 p-5 shadow-2xl backdrop-blur sm:p-6"
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="text-xl font-bold tracking-tight text-ink">{title}</h3>
            <p className="mt-1 text-sm leading-6 text-muted">{description}</p>
          </div>
          <Button type="button" tone="ghost" className="shrink-0 px-2.5" onClick={onClose} aria-label="關閉視窗">
            <X className="h-4 w-4" aria-hidden="true" />
          </Button>
        </div>
        <div className="mt-5">{children}</div>
        {footer ? <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">{footer}</div> : null}
      </div>
    </div>
  );
}

/** Converts stored decimal rate (e.g. 0.003) to display percentage string (e.g. "0.3"). */
function rateToDisplay(value: number) {
  return (value * 100).toFixed(4).replace(/\.?0+$/, "");
}

/** Converts user-entered percentage string (e.g. "0.3") to stored decimal (e.g. 0.003). */
function displayToRate(value: string) {
  return Number(value) / 100;
}

type TaxDraft = Pick<UserSettings, "stock_tax_rate" | "day_trade_tax_rate" | "etf_tax_rate" | "bond_etf_tax_rate">;
type FeeDraft = Pick<UserSettings, "commission_discount_rate" | "base_commission_rate" | "minimum_fee" | "odd_lot_minimum_fee" | "cash_dividend_transfer_fee">;

const defaultSettings: UserSettings = {
  commission_discount_rate: 1,
  base_commission_rate: 0.001425,
  minimum_fee: 20,
  odd_lot_minimum_fee: 1,
  cash_dividend_transfer_fee: 10,
  stock_tax_rate: 0.003,
  day_trade_tax_rate: 0.0015,
  etf_tax_rate: 0.001,
  bond_etf_tax_rate: 0,
};

export function SettingsPage() {
  const { data, isLoading } = useSettings();
  const adminCapabilities = useAdminCapabilities();
  const transactions = useTransactions();
  const cashflows = useCashflows();
  const { session, signOut, updatePassword } = useAuth();

  const [taxDraft, setTaxDraft] = useState<TaxDraft>({
    stock_tax_rate: defaultSettings.stock_tax_rate,
    day_trade_tax_rate: defaultSettings.day_trade_tax_rate,
    etf_tax_rate: defaultSettings.etf_tax_rate,
    bond_etf_tax_rate: defaultSettings.bond_etf_tax_rate,
  });
  const [feeDraft, setFeeDraft] = useState<FeeDraft>({
    commission_discount_rate: defaultSettings.commission_discount_rate,
    base_commission_rate: defaultSettings.base_commission_rate,
    minimum_fee: defaultSettings.minimum_fee,
    odd_lot_minimum_fee: defaultSettings.odd_lot_minimum_fee,
    cash_dividend_transfer_fee: defaultSettings.cash_dividend_transfer_fee,
  });

  const [isTaxOpen, setIsTaxOpen] = useState(false);
  const [isFeeOpen, setIsFeeOpen] = useState(false);
  const [isPasswordOpen, setIsPasswordOpen] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [importMessage, setImportMessage] = useState<string | null>(null);
  const [taxMessage, setTaxMessage] = useState<string | null>(null);
  const [feeMessage, setFeeMessage] = useState<string | null>(null);
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const invalidateQueries = useInvalidateQueries();
  const current = { ...defaultSettings, ...data };

  const taxMutation = useMutation({
    mutationFn: async (patch: TaxDraft) =>
      api.put("/settings", { ...current, ...patch }),
    onSuccess: async () => {
      await invalidateQueries([queryKeys.settings]);
      setTaxMessage("設定已更新。");
      setIsTaxOpen(false);
    },
    onError: () => setTaxMessage("更新失敗，請稍後再試。"),
  });

  const feeMutation = useMutation({
    mutationFn: async (patch: FeeDraft) =>
      api.put("/settings", { ...current, ...patch }),
    onSuccess: async () => {
      await invalidateQueries([queryKeys.settings]);
      setFeeMessage("設定已更新。");
      setIsFeeOpen(false);
    },
    onError: () => setFeeMessage("更新失敗，請稍後再試。"),
  });

  const importMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return (
        await api.post("/export/import", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        })
      ).data as {
        transactions_imported: number;
        cashflows_imported: number;
      };
    },
    onSuccess: async (result) => {
      setImportMessage(`已匯入 ${result.transactions_imported} 筆交易紀錄、${result.cashflows_imported} 筆資金異動。`);
      await invalidateQueries([queryKeys.settings, ...portfolioQueryKeys]);
      if (fileInputRef.current) fileInputRef.current.value = "";
    },
    onError: () => {
      setImportMessage("匯入失敗，請確認檔案格式是否為系統匯出的 Excel。");
      if (fileInputRef.current) fileInputRef.current.value = "";
    },
  });

  const passwordMutation = useMutation({
    mutationFn: async ({ currentPassword, newPassword }: { currentPassword: string; newPassword: string }) => {
      await updatePassword(currentPassword, newPassword);
    },
    onSuccess: () => {
      setPasswordMessage("密碼已更新。");
      setIsPasswordOpen(false);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    },
    onError: (error: unknown) => {
      setPasswordMessage(error instanceof Error ? error.message : "密碼更新失敗。");
    },
  });

  useEffect(() => {
    if (data) {
      setTaxDraft({
        stock_tax_rate: data.stock_tax_rate,
        day_trade_tax_rate: data.day_trade_tax_rate,
        etf_tax_rate: data.etf_tax_rate,
        bond_etf_tax_rate: data.bond_etf_tax_rate,
      });
      setFeeDraft({
        commission_discount_rate: data.commission_discount_rate,
        base_commission_rate: data.base_commission_rate,
        minimum_fee: data.minimum_fee,
        odd_lot_minimum_fee: data.odd_lot_minimum_fee,
        cash_dividend_transfer_fee: data.cash_dividend_transfer_fee ?? defaultSettings.cash_dividend_transfer_fee,
      });
    }
  }, [data]);

  const hasUserData = (transactions.data?.total ?? 0) > 0 || (cashflows.data?.length ?? 0) > 0;
  const exportLoading = transactions.isLoading || cashflows.isLoading;
  const exportLabel = exporting ? "匯出中..." : exportLoading ? "確認資料中..." : hasUserData ? "匯出 Excel" : "匯出 Excel 範本";
  const exportHint = exportLoading
    ? "正在確認目前帳號是否已有交易紀錄或資金異動資料。"
    : hasUserData
      ? "下載包含交易紀錄與資金異動的 Excel 檔案。"
      : "目前沒有資料，將匯出可直接填寫的 Excel 範本。";
  const currentAccount = session?.user.email ?? session?.user.id ?? "未提供";

  const handleExport = async () => {
    setExporting(true);
    try {
      const response = await api.get("/export", { responseType: "blob" });
      downloadFile(response.data, "stocker_export.xlsx");
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

  const openTaxDialog = () => {
    setTaxMessage(null);
    if (data) setTaxDraft({ stock_tax_rate: data.stock_tax_rate, day_trade_tax_rate: data.day_trade_tax_rate, etf_tax_rate: data.etf_tax_rate, bond_etf_tax_rate: data.bond_etf_tax_rate });
    setIsTaxOpen(true);
  };

  const openFeeDialog = () => {
    setFeeMessage(null);
    if (data) setFeeDraft({
      commission_discount_rate: data.commission_discount_rate,
      base_commission_rate: data.base_commission_rate,
      minimum_fee: data.minimum_fee,
      odd_lot_minimum_fee: data.odd_lot_minimum_fee,
      cash_dividend_transfer_fee: data.cash_dividend_transfer_fee ?? defaultSettings.cash_dividend_transfer_fee,
    });
    setIsFeeOpen(true);
  };

  const openPasswordDialog = () => {
    setPasswordMessage(null);
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
    setIsPasswordOpen(true);
  };

  const handlePasswordSubmit = () => {
    setPasswordMessage(null);
    if (!currentPassword) { setPasswordMessage("請輸入目前密碼。"); return; }
    if (newPassword.length < 6) { setPasswordMessage("新密碼至少需要 6 個字元。"); return; }
    if (newPassword !== confirmPassword) { setPasswordMessage("兩次輸入的密碼不一致。"); return; }
    passwordMutation.mutate({ currentPassword, newPassword });
  };

  if (isLoading) return <SkeletonBlock label="載入設定中..." />;

  return (
    <section className="space-y-5">
      <PageHeader
        eyebrow="SETTINGS"
        title="設定"
        description="調整會影響後續交易計算的全域設定。"
        action={
          adminCapabilities.data?.is_admin ? (
            <Link to="/admin" aria-label="管理者後台">
              <Button tone="secondary">管理者後台</Button>
            </Link>
          ) : null
        }
      />

      {/* Row 1: Tax and fee settings */}
      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <div className="flex h-full flex-col gap-4">
            <div className="flex items-start gap-3">
              <span className="rounded-2xl bg-teal-50 p-3 text-accent">
                <Receipt className="h-5 w-5" aria-hidden="true" />
              </span>
              <div className="min-w-0 flex-1">
                <h2 className="text-lg font-bold text-ink">交易稅設定</h2>
                <p className="mt-1 text-sm leading-6 text-muted">設定每筆交易的稅率，系統將依稅率自動計算稅額。</p>
                {taxMessage ? <p className="mt-2 text-sm font-medium text-accent">{taxMessage}</p> : null}
              </div>
            </div>
            <div className="mt-auto flex flex-col gap-3 rounded-2xl border border-line bg-white/75 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">目前稅率</p>
                <p className="mt-1 text-2xl font-bold text-accent">{percent(current.stock_tax_rate)}</p>
              </div>
              <Button tone="ghost" className="w-full shrink-0 whitespace-nowrap !text-accent hover:!bg-teal-50 hover:!text-teal-800 sm:w-auto" onClick={openTaxDialog}>
                調整交易稅
              </Button>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex h-full flex-col gap-4">
            <div className="flex items-start gap-3">
              <span className="rounded-2xl bg-teal-50 p-3 text-accent">
                <SlidersHorizontal className="h-5 w-5" aria-hidden="true" />
              </span>
              <div className="min-w-0 flex-1">
                <h2 className="text-lg font-bold text-ink">手續費設定</h2>
                <p className="mt-1 text-sm leading-6 text-muted">設定交易手續費的折數，系統將依折數計算手續費金額。</p>
                {feeMessage ? <p className="mt-2 text-sm font-medium text-accent">{feeMessage}</p> : null}
              </div>
            </div>
            <div className="mt-auto flex flex-col gap-3 rounded-2xl border border-line bg-white/75 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">目前折數</p>
                <p className="mt-1 text-2xl font-bold text-accent">{percent(current.commission_discount_rate)}</p>
              </div>
              <Button tone="ghost" className="w-full shrink-0 whitespace-nowrap !text-accent hover:!bg-teal-50 hover:!text-teal-800 sm:w-auto" onClick={openFeeDialog}>
                調整手續費
              </Button>
            </div>
          </div>
        </Card>
      </div>

      {/* Row 2: Export / Import */}
      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <div className="flex h-full flex-col gap-4">
            <div className="flex items-start gap-3">
              <span className="rounded-2xl bg-amber-50 p-3 text-amber-700">
                <Download className="h-5 w-5" aria-hidden="true" />
              </span>
              <div className="min-w-0 flex-1">
                <h2 className="text-lg font-bold text-ink">匯出資料</h2>
                <p className="mt-1 text-sm text-muted">{exportHint}</p>
              </div>
            </div>
            <div className="mt-auto flex flex-col gap-3 rounded-2xl border border-line bg-white/75 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Excel</p>
                <p className="mt-1 text-sm font-medium text-ink">{exportLabel}</p>
              </div>
              <Button
                tone="ghost"
                className="w-full shrink-0 whitespace-nowrap !text-accent hover:!bg-teal-50 hover:!text-teal-800 sm:w-auto"
                disabled={exporting || exportLoading}
                onClick={handleExport}
              >
                {exportLabel}
              </Button>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex h-full flex-col gap-4">
            <div className="flex items-start gap-3">
              <span className="rounded-2xl bg-emerald-50 p-3 text-emerald-700">
                <Upload className="h-5 w-5" aria-hidden="true" />
              </span>
              <div className="min-w-0 flex-1">
                <h2 className="text-lg font-bold text-ink">匯入資料</h2>
                <p className="mt-1 text-sm text-muted">上傳系統匯出的 Excel，將覆蓋目前帳號的交易紀錄與資金異動資料。</p>
                {importMessage ? <p className="mt-2 text-sm font-medium text-accent">{importMessage}</p> : null}
              </div>
            </div>
            <div className="mt-auto flex flex-col gap-3 rounded-2xl border border-line bg-white/75 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">上傳 Excel</p>
                <p className="mt-1 text-sm font-medium text-ink">支援系統匯出的檔案格式。</p>
              </div>
              <div>
                <input ref={fileInputRef} type="file" accept=".xlsx" className="hidden" onChange={(event) => void handleImportSelect(event)} />
                <Button
                  tone="ghost"
                  className="w-full shrink-0 whitespace-nowrap !text-accent hover:!bg-teal-50 hover:!text-teal-800 sm:w-auto"
                  disabled={importMutation.isPending}
                  onClick={() => fileInputRef.current?.click()}
                >
                  {importMutation.isPending ? "匯入中..." : "選擇 Excel"}
                </Button>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Row 3: Password / Logout */}
      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <div className="flex h-full flex-col gap-4">
            <div className="flex items-start gap-3">
              <span className="rounded-2xl bg-sky-50 p-3 text-sky-700">
                <KeyRound className="h-5 w-5" aria-hidden="true" />
              </span>
              <div className="min-w-0 flex-1">
                <h2 className="text-lg font-bold text-ink">更改密碼</h2>
                <p className="mt-1 text-sm text-muted">更新目前帳號的登入密碼，點按後會以小視窗處理。</p>
                {passwordMessage ? <p className="mt-2 text-sm font-medium text-accent">{passwordMessage}</p> : null}
              </div>
            </div>
            <div className="mt-auto flex flex-col gap-3 rounded-2xl border border-line bg-white/75 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">安全設定</p>
                <p className="mt-1 text-sm font-medium text-ink">按下後填入目前密碼與新密碼。</p>
              </div>
              <Button tone="ghost" className="w-full shrink-0 whitespace-nowrap !text-accent hover:!bg-teal-50 hover:!text-teal-800 sm:w-auto" onClick={openPasswordDialog}>
                更改密碼
              </Button>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex h-full flex-col gap-4">
            <div className="flex items-start gap-3">
              <span className="rounded-2xl bg-rose-50 p-3 text-rose-500">
                <LogOut className="h-5 w-5" aria-hidden="true" />
              </span>
              <div className="min-w-0 flex-1">
                <h2 className="text-lg font-bold text-ink">帳戶登出</h2>
                <p className="mt-1 text-sm text-muted">結束目前的登入工作階段。</p>
              </div>
            </div>
            <div className="mt-auto flex flex-col gap-3 rounded-2xl border border-line bg-white/75 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">目前帳號</p>
                <p className="mt-1 truncate text-sm font-medium text-ink">{currentAccount}</p>
              </div>
              <Button tone="danger" className="w-full shrink-0 whitespace-nowrap sm:w-auto" onClick={() => void signOut()}>
                登出
              </Button>
            </div>
          </div>
        </Card>
      </div>

      {/* Tax modal */}
      <DialogShell
        open={isTaxOpen}
        title="調整交易稅設定"
        description="輸入稅率百分比（例如 0.3 代表 0.3%）。"
        onClose={() => setIsTaxOpen(false)}
        footer={
          <>
            <Button type="button" tone="secondary" onClick={() => setIsTaxOpen(false)}>取消</Button>
            <Button type="submit" form="tax-form" disabled={taxMutation.isPending}>
              {taxMutation.isPending ? "儲存中..." : "儲存"}
            </Button>
          </>
        }
      >
        <form
          id="tax-form"
          className="space-y-4"
          onSubmit={(e) => { e.preventDefault(); taxMutation.mutate(taxDraft); }}
        >
          <Field
            label="一般股票賣出稅率 (%)"
            type="number"
            min="0"
            step="0.001"
            value={rateToDisplay(taxDraft.stock_tax_rate)}
            onChange={(e) => setTaxDraft((p) => ({ ...p, stock_tax_rate: displayToRate(e.target.value) }))}
            hint="預設 0.3（即 0.3%）"
          />
          <Field
            label="當沖賣出稅率 (%)"
            type="number"
            min="0"
            step="0.001"
            value={rateToDisplay(taxDraft.day_trade_tax_rate)}
            onChange={(e) => setTaxDraft((p) => ({ ...p, day_trade_tax_rate: displayToRate(e.target.value) }))}
            hint="預設 0.15（即 0.15%）"
          />
          <Field
            label="ETF 賣出稅率 (%)"
            type="number"
            min="0"
            step="0.001"
            value={rateToDisplay(taxDraft.etf_tax_rate)}
            onChange={(e) => setTaxDraft((p) => ({ ...p, etf_tax_rate: displayToRate(e.target.value) }))}
            hint="適用 00 開頭（非 B 結尾）ETF，預設 0.1"
          />
          <Field
            label="債券ETF稅率 (%)"
            type="number"
            min="0"
            step="0.001"
            value={rateToDisplay(taxDraft.bond_etf_tax_rate)}
            onChange={(e) => setTaxDraft((p) => ({ ...p, bond_etf_tax_rate: displayToRate(e.target.value) }))}
            hint="適用 00 開頭且 B 結尾的 ETF，預設 0（即豁免）"
          />
        </form>
      </DialogShell>

      {/* Fee modal */}
      <DialogShell
        open={isFeeOpen}
        title="調整手續費設定"
        description="設定手續費基本費率、折數與最低收費。"
        onClose={() => setIsFeeOpen(false)}
        footer={
          <>
            <Button type="button" tone="secondary" onClick={() => setIsFeeOpen(false)}>取消</Button>
            <Button type="submit" form="fee-form" disabled={feeMutation.isPending}>
              {feeMutation.isPending ? "儲存中..." : "儲存"}
            </Button>
          </>
        }
      >
        <form
          id="fee-form"
          className="space-y-4"
          onSubmit={(e) => { e.preventDefault(); feeMutation.mutate(feeDraft); }}
        >
          <Field
            label="手續費基本費率 (%)"
            type="number"
            min="0"
            step="0.0001"
            value={rateToDisplay(feeDraft.base_commission_rate)}
            onChange={(e) => setFeeDraft((p) => ({ ...p, base_commission_rate: displayToRate(e.target.value) }))}
            hint="預設 0.1425（即 0.1425%）"
          />
          <Field
            label="手續費折數 (%)"
            type="number"
            min="0"
            max="100"
            step="1"
            value={rateToDisplay(feeDraft.commission_discount_rate)}
            onChange={(e) => setFeeDraft((p) => ({ ...p, commission_discount_rate: displayToRate(e.target.value) }))}
            hint="例如 60 代表六折，100 代表無折扣"
          />
          <Field
            label="整股最低手續費 (TWD)"
            type="number"
            min="0"
            step="1"
            value={feeDraft.minimum_fee}
            onChange={(e) => setFeeDraft((p) => ({ ...p, minimum_fee: Number(e.target.value) }))}
            hint="預設 20 元"
          />
          <Field
            label="零股最低手續費 (TWD)"
            type="number"
            min="0"
            step="1"
            value={feeDraft.odd_lot_minimum_fee}
            onChange={(e) => setFeeDraft((p) => ({ ...p, odd_lot_minimum_fee: Number(e.target.value) }))}
            hint="預設 1 元"
          />
          <Field
            label="現金股利匯款手續費 (TWD)"
            type="number"
            min="0"
            step="1"
            value={feeDraft.cash_dividend_transfer_fee}
            onChange={(e) => setFeeDraft((p) => ({ ...p, cash_dividend_transfer_fee: Number(e.target.value) }))}
            hint="預設 10 元"
          />
        </form>
      </DialogShell>

      {/* Password modal */}
      <DialogShell
        open={isPasswordOpen}
        title="變更登入密碼"
        description="請先輸入目前密碼，再設定新的密碼。"
        onClose={() => setIsPasswordOpen(false)}
        footer={
          <>
            <Button type="button" tone="secondary" onClick={() => setIsPasswordOpen(false)}>取消</Button>
            <Button type="submit" form="password-form" disabled={passwordMutation.isPending}>
              {passwordMutation.isPending ? "更新中..." : "更新密碼"}
            </Button>
          </>
        }
      >
        <form
          id="password-form"
          className="space-y-4"
          onSubmit={(e) => { e.preventDefault(); handlePasswordSubmit(); }}
        >
          {passwordMessage ? <p className="rounded-2xl border border-line bg-white/75 px-3 py-2 text-sm text-accent">{passwordMessage}</p> : null}
          <Field label="目前密碼" type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} />
          <Field label="新密碼" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
          <Field label="確認新密碼" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
          <p className="text-xs text-muted">新密碼至少需要 6 個字元。</p>
        </form>
      </DialogShell>
    </section>
  );
}
