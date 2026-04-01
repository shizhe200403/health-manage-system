export type OpsIdentity = Record<string, any> | null | undefined;
export type OpsScope = "manager" | "operator";

export function isOpsManager(user: OpsIdentity) {
  return Boolean(user && (user.role === "admin" || user.is_superuser || user.is_staff));
}

export function hasOpsAccess(user: OpsIdentity) {
  return isOpsManager(user) || user?.role === "auditor";
}

export function canAccessOpsScope(user: OpsIdentity, scope: OpsScope) {
  return scope === "manager" ? isOpsManager(user) : hasOpsAccess(user);
}

export function readStoredOpsIdentity() {
  return {
    role: localStorage.getItem("user_role") || "",
    is_superuser: localStorage.getItem("user_is_superuser") === "true",
    is_staff: localStorage.getItem("user_is_staff") === "true",
  };
}

export function resolveOpsHome(user: OpsIdentity) {
  if (isOpsManager(user)) return "/ops";
  if (hasOpsAccess(user)) return "/ops/reports";
  return "/";
}
