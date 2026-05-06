import { queryKeys, useApiQuery } from "../../platform/api/query";
import type { UserSettings } from "./types";

export function useSettings() {
  return useApiQuery<UserSettings>(queryKeys.settings, "/settings");
}
