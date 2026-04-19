export type ProjectStatus = "draft" | "active" | "on_hold" | "completed" | "cancelled" | "archived";

export type Project = {
  id: string;
  company_id: string;
  name: string;
  code: string | null;
  description: string | null;
  objective: string | null;
  status: ProjectStatus;
  start_date: string | null;
  due_date: string | null;
  owner_user_id: string | null;
  created_at: string;
  updated_at: string;
};

export type ProjectCreateInput = {
  company_id: string;
  name: string;
  code?: string;
  description?: string;
  objective?: string;
  process_id?: string;
  status: ProjectStatus;
};
