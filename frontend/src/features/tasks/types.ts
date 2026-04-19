export type TaskStatus = "pending" | "in_progress" | "review" | "completed" | "blocked";
export type TaskPriority = "low" | "medium" | "high" | "critical";

export type AssignedTo = {
  type: "user" | "role";
  id: string;
};

export type Task = {
  id: string;
  company_id: string;
  project_id: string;
  process_step_id: string | null;
  parent_task_id: string | null;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  assigned_to: AssignedTo | null;
  assignee_user_id: string | null;
  assignee_role_id: string | null;
  due_date: string | null;
  started_at: string | null;
  completed_at: string | null;
  requires_evidence: boolean;
  requires_approval: boolean;
  created_at: string;
  updated_at: string;
};

export type TaskCreateInput = {
  assigned_to?: AssignedTo | null;
  company_id: string;
  description?: string;
  priority: TaskPriority;
  project_id: string;
  requires_approval: boolean;
  requires_evidence: boolean;
  status: TaskStatus;
  title: string;
};

export type TaskComment = {
  id: string;
  company_id: string;
  task_id: string;
  author_user_id: string | null;
  body: string;
  created_at: string;
  updated_at: string;
};

export type TaskCommentCreateInput = {
  author_user_id?: string;
  body: string;
  company_id: string;
};

export type TaskAttachment = {
  id: string;
  company_id: string;
  task_id: string;
  file_name: string;
  storage_key: string;
  content_type: string | null;
  size_bytes: number;
  uploaded_by_user_id: string | null;
  created_at: string;
};

export type TaskAttachmentCreateInput = {
  company_id: string;
  content_type?: string;
  file_name: string;
  size_bytes: number;
  storage_key: string;
  uploaded_by_user_id?: string;
};
