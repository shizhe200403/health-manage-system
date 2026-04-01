import http from "./http";

export async function listAdminOperationLogs(params?: Record<string, unknown>) {
  const { data } = await http.get("/admin/operation-logs/", { params });
  return data;
}
