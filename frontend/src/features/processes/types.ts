export type ProcessStatus = "draft" | "published" | "archived";

export type Process = {
  id: string;
  company_id: string;
  name: string;
  code: string | null;
  objective: string | null;
  scope: string | null;
  owner_user_id: string | null;
  version_label: string | null;
  status: ProcessStatus;
  created_at: string;
  updated_at: string;
};

export type ProcessCreateInput = {
  code?: string;
  company_id: string;
  name: string;
  objective?: string;
  scope?: string;
  status: ProcessStatus;
  version_label?: string;
};

export type ProcessStep = {
  id: string;
  company_id: string;
  process_id: string;
  step_order: number;
  name: string;
  description: string | null;
  responsible_role_id: string | null;
  responsible_user_id: string | null;
  instruction_summary: string | null;
  expected_duration_hours: number | null;
  sla_hours: number | null;
  requires_evidence: boolean;
  requires_approval: boolean;
  created_at: string;
  updated_at: string;
};

export type ProcessStepCreateInput = {
  company_id: string;
  description?: string;
  name: string;
  process_id: string;
  requires_approval: boolean;
  requires_evidence: boolean;
  responsible_role_id?: string;
  responsible_user_id?: string;
  step_order: number;
};
