import http from "./http";

export interface AdminWorkbenchLink {
  path: string;
  query?: Record<string, unknown>;
}

export interface AdminOperationsSummary {
  users_total: number;
  users_active: number;
  users_pending: number;
  recipes_total: number;
  recipes_pending: number;
  recipes_rejected: number;
  posts_total: number;
  posts_pending: number;
  posts_rejected: number;
  pending_reports: number;
  hidden_comments: number;
  meal_records_last_7_days: number;
  active_record_users_last_7_days: number;
  report_tasks_total: number;
  report_tasks_processing: number;
  report_tasks_failed: number;
  report_tasks_completed: number;
}

export interface AdminQueueSummary {
  key: string;
  label: string;
  count: number;
  tone: string;
  title: string;
  description: string;
  link: AdminWorkbenchLink;
}

export interface AdminRecentWorkItem {
  key: string;
  label: string;
  title: string;
  description: string;
  tone: string;
  created_at: string | null;
  link: AdminWorkbenchLink;
}

export interface AdminRecentReportTask {
  task_id: number;
  report_type: string;
  status: string;
  file_url: string;
  start_date: string | null;
  end_date: string | null;
  generated_at: string | null;
  user: {
    id: number;
    username: string;
    nickname: string;
    display_name: string;
  };
}

export interface AdminOperationsOverviewData {
  summary: AdminOperationsSummary;
  queue_summaries: AdminQueueSummary[];
  recent_work_items: AdminRecentWorkItem[];
  recent_tasks: AdminRecentReportTask[];
}

export async function getAdminOperationsOverview() {
  const { data } = await http.get("/reports/admin/overview/");
  return data as { data?: AdminOperationsOverviewData };
}
