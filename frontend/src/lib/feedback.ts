export { ElMessage } from "element-plus/es/components/message/index.mjs";
export { ElMessageBox } from "element-plus/es/components/message-box/index.mjs";

import { ElNotification } from "element-plus";

export function notifyLoadError(subject: string) {
  ElNotification.error({ title: "加载失败", message: `${subject}加载失败，请稍后重试`, duration: 3000 });
}

export function notifyActionSuccess(message: string) {
  ElNotification.success({ title: "操作成功", message, duration: 2500 });
}

export function notifyActionError(action: string) {
  ElNotification.error({ title: "操作失败", message: `${action}失败，请稍后重试`, duration: 3000 });
}

export function notifyWarning(message: string) {
  ElNotification.warning({ title: "提示", message, duration: 3000 });
}

export function notifyErrorMessage(message: string) {
  ElNotification.error({ title: "错误", message, duration: 3000 });
}

export function extractApiErrorMessage(error: unknown, fallback = "操作失败，请稍后重试") {
  const responseData = (error as { response?: { data?: any } })?.response?.data;

  if (typeof responseData === "string" && responseData.trim()) {
    return responseData;
  }

  const candidates = [
    responseData?.message,
    responseData?.detail,
    responseData?.error,
    Array.isArray(responseData?.non_field_errors) ? responseData.non_field_errors[0] : null,
  ];

  for (const value of candidates) {
    if (typeof value === "string" && value.trim()) {
      return value;
    }
  }

  if (responseData && typeof responseData === "object") {
    for (const value of Object.values(responseData)) {
      if (typeof value === "string" && value.trim()) {
        return value;
      }
      if (Array.isArray(value) && typeof value[0] === "string" && value[0].trim()) {
        return value[0];
      }
    }
  }

  return fallback;
}
