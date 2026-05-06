export type AdminCapabilities = {
  is_admin: boolean;
};

export type AdminOverview = {
  total_users: number;
  users_with_transactions: number;
  users_with_cashflows: number;
  supabase_memory_usage_percent: number | null;
  cpu_busy_percent: number | null;
  disk_usage_percent: number | null;
  connection_rate_percent: number | null;
  active_queries: number | null;
};

export type AdminTableSummary = {
  name: string;
  label: string;
  description: string;
  row_count: number;
};

export type AdminTablePage = {
  table_name: string;
  label: string;
  page: number;
  page_size: number;
  total: number;
  columns: string[];
  items: Array<Record<string, string | number | boolean | null>>;
};
