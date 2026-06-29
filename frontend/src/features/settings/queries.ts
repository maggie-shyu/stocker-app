import { queryKeys, useApiQuery } from "../../platform/api/query";
import type { Feedback, UserSettings } from "./types";

export function useSettings() {
  return useApiQuery<UserSettings>(queryKeys.settings, "/settings");
}

export function useFeedbacks() {
  return useApiQuery<Feedback[]>(queryKeys.feedbacks, "/feedbacks");
}
