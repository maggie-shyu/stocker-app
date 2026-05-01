import { SlidersHorizontal } from "lucide-react";
import { useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { api } from "../api/client";
import { queryKeys, useInvalidateQueries } from "../api/query";
import { Button, Card, PageHeader, SkeletonBlock } from "../components/shared/UI";
import { percent } from "../components/shared/format";
import { useSettings } from "../hooks/queries";

export function Settings() {
  const { data, isLoading } = useSettings();
  const [rate, setRate] = useState(0);
  const invalidateQueries = useInvalidateQueries();
  const mutation = useMutation({
    mutationFn: async (commission_discount_rate: number) =>
      api.put("/settings", { commission_discount_rate }),
    onSuccess: () => invalidateQueries([queryKeys.settings])
  });

  useEffect(() => {
    if (data) setRate(data.commission_discount_rate);
  }, [data]);

  if (isLoading) return <SkeletonBlock label="載入設定中..." />;

  return (
    <section className="max-w-3xl space-y-5">
      <PageHeader
        eyebrow="Preferences"
        title="設定"
        description="調整會影響後續交易計算的全域設定。"
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
    </section>
  );
}
