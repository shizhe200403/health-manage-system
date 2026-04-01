import http from "./http";

export async function getAdminOperationsOverview() {
  const { data } = await http.get("/reports/admin/overview/");
  return data;
}
