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
