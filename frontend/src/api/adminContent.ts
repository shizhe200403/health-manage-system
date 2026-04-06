import http from "./http";

export async function listAdminCommunityPosts(params?: Record<string, unknown>) {
  const { data } = await http.get("/community/admin/posts/", { params });
  return data;
}

export async function getAdminCommunityPostDetail(postId: number) {
  const { data } = await http.get(`/community/admin/posts/${postId}/`);
  return data;
}

export async function updateAdminCommunityPost(postId: number, payload: Record<string, unknown>) {
  const { data } = await http.patch(`/community/admin/posts/${postId}/`, payload);
  return data;
}

export async function bulkUpdateAdminCommunityPosts(payload: { ids: number[]; action: "approve" | "reject" | "archive" }) {
  const { data } = await http.post("/community/admin/posts/bulk/", payload);
  return data;
}

export async function listAdminCommunityReports(params?: Record<string, unknown>) {
  const { data } = await http.get("/community/admin/reports/", { params });
  return data;
}

export async function getAdminCommunityReportDetail(reportId: number) {
  const { data } = await http.get(`/community/admin/reports/${reportId}/`);
  return data;
}

export async function updateAdminCommunityReport(reportId: number, payload: Record<string, unknown>) {
  const { data } = await http.patch(`/community/admin/reports/${reportId}/`, payload);
  return data;
}

export async function bulkUpdateAdminCommunityReports(payload: { ids: number[]; action: "processed" | "rejected" }) {
  const { data } = await http.post("/community/admin/reports/bulk/", payload);
  return data;
}

export interface AdminSensitiveWordRule {
  id: number;
  word: string;
  action: "mask" | "block";
  is_active: boolean;
  note: string;
  created_at: string;
  updated_at: string;
}

export async function listAdminSensitiveWordRules(params?: Record<string, unknown>) {
  const { data } = await http.get("/community/admin/sensitive-words/", { params });
  return data as { data?: { items?: AdminSensitiveWordRule[] } };
}

export async function createAdminSensitiveWordRule(payload: Record<string, unknown>) {
  const { data } = await http.post("/community/admin/sensitive-words/", payload);
  return data as { data?: AdminSensitiveWordRule };
}

export async function updateAdminSensitiveWordRule(ruleId: number, payload: Record<string, unknown>) {
  const { data } = await http.patch(`/community/admin/sensitive-words/${ruleId}/`, payload);
  return data as { data?: AdminSensitiveWordRule };
}

export async function deleteAdminSensitiveWordRule(ruleId: number) {
  const { data } = await http.delete(`/community/admin/sensitive-words/${ruleId}/`);
  return data as { data?: { deleted?: boolean; id?: number } };
}
