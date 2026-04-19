import { apiClient } from "../../shared/api/client";
import type { AuditLog } from "./types";

type AuditLogFilters = {
  action?: string;
  company_id?: string;
  target_id?: string;
  target_type?: string;
};

export function listAuditLogs(filters: AuditLogFilters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) {
      params.set(key, value);
    }
  });
  const query = params.toString();
  return apiClient.get<AuditLog[]>(`/audit-logs${query ? `?${query}` : ""}`);
}
