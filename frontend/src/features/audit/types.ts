export type AuditLog = {
  id: string;
  company_id: string;
  actor_user_id: string | null;
  action: string;
  target_type: string;
  target_id: string;
  summary: string;
  before_data_json: Record<string, unknown> | null;
  after_data_json: Record<string, unknown> | null;
  created_at: string;
};
