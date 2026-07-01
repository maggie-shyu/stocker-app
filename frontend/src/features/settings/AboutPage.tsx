import {
  CheckCircle2,
  ChevronRight,
  HeartHandshake,
  Lightbulb,
  ListChecks,
  Map,
  MessageCircle,
  MessageSquare,
  PanelLeftClose,
  PanelLeftOpen,
  PencilLine,
  Send,
  Trash2,
} from "lucide-react";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

import type { Feedback } from "./types";
import { api } from "../../platform/api/client";
import { queryKeys, useInvalidateQueries } from "../../platform/api/query";
import { Card, PageHeader } from "../../shared/ui/UI";
import { useFeedbacks } from "./queries";

const functionSummary = [
  {
    page: "儀表板",
    description: "快速看目前帳戶的整體狀態，包含本金、現金部位、資產變化和主要損益。",
  },
  {
    page: "持股狀況",
    description: "整理現在手上還持有的股票，幫助我們知道每個部位買了多少、成本是多少、目前表現如何。",
  },
  {
    page: "平倉盈虧",
    description: "回顧已經賣出的交易結果，看每檔股票實際賺了或虧了多少。",
  },
  {
    page: "交易紀錄",
    description: "記下每一筆買進、賣出和股利，也保留當時的想法，之後回頭看才知道自己為什麼做決定。",
  },
  {
    page: "資金異動",
    description: "記錄本金投入和提款，讓投資績效和帳戶現金變化可以分開看清楚。",
  },
  {
    page: "設定",
    description: "調整交易稅、手續費、股利匯款費，也可以匯入匯出資料，讓帳本更符合自己的使用方式。",
  },
];

const feedbackBodyLimit = 500;

export function AboutPage() {
  const feedbacks = useFeedbacks();
  const invalidateQueries = useInvalidateQueries();
  const [isDrawerOpen, setIsDrawerOpen] = useState(true);
  const [subjectDraft, setSubjectDraft] = useState("");
  const [bodyDraft, setBodyDraft] = useState("");
  const [selectedFeedbackId, setSelectedFeedbackId] = useState<string | null>(null);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  const selectedFeedback = feedbacks.data?.find((feedback) => feedback.id === selectedFeedbackId) ?? null;
  const isEditing = selectedFeedback !== null;
  const trimmedSubject = subjectDraft.trim();
  const hasFeedbackChanges = selectedFeedback
    ? trimmedSubject !== selectedFeedback.subject || bodyDraft !== selectedFeedback.body
    : false;

  const createFeedbackMutation = useMutation({
    mutationFn: async (payload: { subject: string; body: string }) => (await api.post<Feedback>("/feedbacks", payload)).data,
    onSuccess: async () => {
      await invalidateQueries([queryKeys.feedbacks]);
      setSubjectDraft("");
      setBodyDraft("");
      setSelectedFeedbackId(null);
      setFeedbackMessage("已送出。");
    },
    onError: () => setFeedbackMessage("送出失敗，請稍後再試。"),
  });

  const updateFeedbackMutation = useMutation({
    mutationFn: async ({ id, subject, body }: { id: string; subject: string; body: string }) =>
      (await api.put<Feedback>(`/feedbacks/${id}`, { subject, body })).data,
    onSuccess: async (updated) => {
      await invalidateQueries([queryKeys.feedbacks]);
      setSubjectDraft(updated.subject);
      setBodyDraft(updated.body);
      setSelectedFeedbackId(updated.id);
      setFeedbackMessage("已更新。");
    },
    onError: () => setFeedbackMessage("更新失敗，請稍後再試。"),
  });

  const deleteFeedbackMutation = useMutation({
    mutationFn: async (id: string) => api.delete(`/feedbacks/${id}`),
    onSuccess: async () => {
      await invalidateQueries([queryKeys.feedbacks]);
      setSubjectDraft("");
      setBodyDraft("");
      setSelectedFeedbackId(null);
      setFeedbackMessage("已刪除。");
    },
    onError: () => setFeedbackMessage("刪除失敗，請稍後再試。"),
  });

  const clearFeedbackDraft = () => {
    setSubjectDraft("");
    setBodyDraft("");
    setSelectedFeedbackId(null);
    setFeedbackMessage(null);
  };

  const handleSend = () => {
    if (!trimmedSubject) return;
    setFeedbackMessage(null);
    createFeedbackMutation.mutate({ subject: trimmedSubject, body: bodyDraft });
  };

  const handleUpdate = () => {
    if (!selectedFeedback || !trimmedSubject || !hasFeedbackChanges) return;
    setFeedbackMessage(null);
    updateFeedbackMutation.mutate({ id: selectedFeedback.id, subject: trimmedSubject, body: bodyDraft });
  };

  const handleDelete = () => {
    if (!selectedFeedback) return;
    setFeedbackMessage(null);
    deleteFeedbackMutation.mutate(selectedFeedback.id);
  };

  const selectFeedback = (feedback: Feedback) => {
    if (selectedFeedbackId === feedback.id) {
      clearFeedbackDraft();
      return;
    }
    setSelectedFeedbackId(feedback.id);
    setSubjectDraft(feedback.subject);
    setBodyDraft(feedback.body);
    setFeedbackMessage(null);
  };

  return (
    <section className="space-y-4 sm:space-y-5">
      <PageHeader
        eyebrow="ABOUT"
        title="關於"
        description="這是一個為懶人設計的股票帳本。"
      />

      <Card className="rounded-[1.75rem] bg-white/90 p-4 shadow-card sm:p-5 lg:p-6" padded={false}>
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div className="flex min-w-0 items-start gap-3 sm:gap-4">
            <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-teal-50 text-accent sm:h-14 sm:w-14">
              <MessageCircle className="h-6 w-6" aria-hidden="true" />
            </span>
            <div className="min-w-0">
              <h2 className="text-xl font-black tracking-tight text-ink sm:text-2xl">意見箱 / 許願池</h2>
              <p className="mt-1 text-sm font-medium leading-6 text-muted">你的回饋，讓「股客」變得更好。</p>
              {feedbackMessage ? <p className="mt-1 text-sm font-semibold text-accent">{feedbackMessage}</p> : null}
            </div>
          </div>
          <div className="flex w-full flex-wrap gap-2 sm:w-auto sm:justify-end">
            {isEditing ? (
              <>
                <button
                  type="button"
                  className="inline-flex min-h-11 flex-1 items-center justify-center gap-2 rounded-2xl border border-line bg-white px-4 py-2 text-sm font-semibold text-muted shadow-sm transition hover:bg-stone-50 hover:text-ink disabled:cursor-not-allowed disabled:opacity-55 sm:flex-none sm:px-6"
                  onClick={clearFeedbackDraft}
                >
                  取消
                </button>
                <button
                  type="button"
                  className="inline-flex min-h-11 flex-1 items-center justify-center gap-2 rounded-2xl border border-rose-100 bg-white px-4 py-2 text-sm font-semibold text-rose-700 shadow-sm transition hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-55 sm:flex-none sm:px-6"
                  disabled={deleteFeedbackMutation.isPending}
                  onClick={handleDelete}
                >
                  <Trash2 className="h-4 w-4" aria-hidden="true" />
                  刪除
                </button>
                <button
                  type="button"
                  className="inline-flex min-h-11 flex-1 items-center justify-center gap-2 rounded-2xl bg-accent px-4 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-55 sm:flex-none sm:px-6"
                  disabled={!trimmedSubject || !hasFeedbackChanges || updateFeedbackMutation.isPending}
                  onClick={handleUpdate}
                >
                  <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
                  更新
                </button>
              </>
            ) : (
              <>
                <button
                  type="button"
                  className="inline-flex min-h-11 flex-1 items-center justify-center gap-2 rounded-2xl border border-line bg-white px-4 py-2 text-sm font-semibold text-muted shadow-sm transition hover:bg-stone-50 hover:text-ink disabled:cursor-not-allowed disabled:opacity-55 sm:flex-none sm:px-6"
                  onClick={clearFeedbackDraft}
                >
                  取消
                </button>
                <button
                  type="button"
                  className="inline-flex min-h-11 flex-1 items-center justify-center gap-2 rounded-2xl bg-accent px-4 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-55 sm:flex-none sm:px-6"
                  disabled={!trimmedSubject || createFeedbackMutation.isPending}
                  onClick={handleSend}
                >
                  <Send className="h-4 w-4" aria-hidden="true" />
                  送出
                </button>
              </>
            )}
          </div>
        </div>

        <div className="mt-5 grid gap-4 lg:grid-cols-[minmax(17rem,24rem)_minmax(0,1fr)]">
          <div
            className={`overflow-hidden rounded-2xl border border-line bg-white/75 shadow-sm ${
              isDrawerOpen ? "min-h-[14rem]" : "min-h-0 lg:min-h-[14rem]"
            }`}
          >
            <div className="flex min-h-14 items-center justify-between px-4 py-3">
              <h3 className={`text-base font-bold text-ink ${isDrawerOpen ? "" : "lg:hidden"}`}>過去的回饋</h3>
              <button
                type="button"
                aria-label="過去的回饋"
                aria-expanded={isDrawerOpen}
                className="inline-flex h-9 w-9 items-center justify-center rounded-xl text-muted transition hover:bg-white hover:text-ink"
                onClick={() => setIsDrawerOpen((current) => !current)}
              >
                {isDrawerOpen ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeftOpen className="h-4 w-4" />}
              </button>
            </div>
            {isDrawerOpen ? (
              <div className="max-h-72 space-y-2 overflow-y-auto px-3 pb-3 sm:max-h-64">
                {feedbacks.isLoading ? (
                  <p className="rounded-2xl border border-line bg-white px-4 py-3 text-sm text-muted">載入中...</p>
                ) : feedbacks.data?.length ? (
                  feedbacks.data.map((feedback) => (
                    <button
                      key={feedback.id}
                      type="button"
                      aria-label={feedback.subject}
                      className={`flex w-full items-center gap-3 rounded-2xl border px-3 py-3 text-left text-sm transition ${
                        selectedFeedbackId === feedback.id
                          ? "border-accent bg-teal-50/80 shadow-sm"
                          : "border-line bg-white text-muted hover:border-teal-500 hover:bg-teal-50/40 hover:text-ink"
                      }`}
                      onClick={() => selectFeedback(feedback)}
                    >
                      <span className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-teal-50 text-accent">
                        <Lightbulb className="h-5 w-5" aria-hidden="true" />
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block truncate font-bold text-ink">{feedback.subject}</span>
                        <span className="mt-0.5 block truncate text-muted">{feedback.body || "未填寫內容"}</span>
                      </span>
                      <ChevronRight className="h-4 w-4 shrink-0 text-muted" aria-hidden="true" />
                    </button>
                  ))
                ) : (
                  <p className="rounded-2xl border border-line bg-white px-4 py-3 text-sm text-muted">還沒有送出的內容。</p>
                )}
              </div>
            ) : null}
          </div>

          <div className="min-w-0 rounded-2xl border border-line bg-white/75 p-3 shadow-sm sm:p-4">
            <div className="relative">
              <PencilLine className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted" aria-hidden="true" />
              <input
                value={subjectDraft}
                onChange={(event) => {
                  setSubjectDraft(event.target.value);
                  setFeedbackMessage(null);
                }}
                placeholder="標題"
                className="min-h-14 w-full rounded-2xl border border-line bg-white/80 py-3 pl-12 pr-4 text-sm font-medium text-ink shadow-sm transition placeholder:text-stone-400 focus:border-accent focus:bg-white focus:outline-none focus:ring-2 focus:ring-accent/15"
              />
            </div>
            <div className="relative mt-3">
              <MessageSquare className="pointer-events-none absolute left-4 top-5 h-5 w-5 text-muted" aria-hidden="true" />
              <textarea
                value={bodyDraft}
                maxLength={feedbackBodyLimit}
                onChange={(event) => {
                  setBodyDraft(event.target.value);
                  setFeedbackMessage(null);
                }}
                placeholder="想跟我們說..."
                className="min-h-[11rem] w-full resize-none rounded-2xl border border-line bg-white/80 py-4 pl-12 pr-4 text-sm leading-7 text-ink shadow-sm transition placeholder:text-stone-400 focus:border-accent focus:bg-white focus:outline-none focus:ring-2 focus:ring-accent/15 sm:min-h-[10rem]"
              />
              <span className="pointer-events-none absolute bottom-3 right-4 text-xs font-semibold text-muted">
                {bodyDraft.length} / {feedbackBodyLimit}
              </span>
            </div>
          </div>
        </div>
      </Card>

      <div className="space-y-4">
        <Card>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
            <span className="w-fit rounded-2xl bg-rose-50 p-3 text-rose-600">
              <HeartHandshake className="h-5 w-5" aria-hidden="true" />
            </span>
            <div className="min-w-0 flex-1">
              <h2 className="text-lg font-bold text-ink">開發動機</h2>
              <p className="mt-3 text-sm leading-7 text-muted">
                想要一個簡單、好用、可以一站式管理股票帳本的工具。不只可以把自己的股票交易記清楚，也可以實時掌握整個帳戶的狀態。
              </p>
              <p className="mt-3 text-sm leading-7 text-muted">
                不再把資訊分散在券商 App、試算表和零散筆記裡，而是讓過往的經驗和現在的財務健康被整合起來，在投資決策的當下幫助我們。
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
            <span className="w-fit rounded-2xl bg-teal-50 p-3 text-accent">
              <ListChecks className="h-5 w-5" aria-hidden="true" />
            </span>
            <div className="min-w-0 flex-1">
              <h2 className="text-lg font-bold text-ink">功能摘要</h2>
              <ul className="mt-3 space-y-2 text-sm leading-6 text-muted">
                {functionSummary.map((item) => (
                  <li key={item.page} className="flex gap-2">
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                    <span>
                      <span className="font-semibold text-ink">{item.page}：</span>
                      {item.description}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
            <span className="w-fit rounded-2xl bg-amber-50 p-3 text-amber-700">
              <Map className="h-5 w-5" aria-hidden="true" />
            </span>
            <div className="min-w-0 flex-1">
              <h2 className="text-lg font-bold text-ink">產品路線</h2>
              <p className="mt-3 text-sm leading-7 text-muted">
                目前還在持續開發中。之後想加入更多技術分析資訊，也希望慢慢嘗試把模型放進來，讓這個帳本不只記錄發生過的事，也能幫助我們更有脈絡地觀察市場和自己的交易節奏。
              </p>
            </div>
          </div>
        </Card>
      </div>
    </section>
  );
}
