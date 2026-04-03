import http from "./http";

export async function listAdminUsers(params?: Record<string, unknown>) {
  const { data } = await http.get("/accounts/admin/users/", { params });
  return data;
}

export async function getAdminUserDetail(userId: number) {
  const { data } = await http.get(`/accounts/admin/users/${userId}/`);
  return data;
}

export async function updateAdminUser(userId: number, payload: Record<string, unknown>) {
  const { data } = await http.patch(`/accounts/admin/users/${userId}/`, payload);
  return data;
}

export async function bulkUpdateAdminUsers(payload: { ids: number[]; status: "active" | "disabled" }) {
  const { data } = await http.post("/accounts/admin/users/bulk/", payload);
  return data;
}

export async function setUserPlan(userId: number, plan: "free" | "pro") {
  const { data } = await http.post(`/accounts/admin/users/${userId}/plan/`, { plan });
  return data;
}
