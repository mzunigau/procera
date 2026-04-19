import type { Project, ProjectCreateInput } from "../projects/types";

export type TemplateType = "project" | "process" | "task_set";

export type Template = {
  id: string;
  company_id: string;
  template_type: TemplateType;
  name: string;
  description: string | null;
  payload_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type TemplateFromSourceInput = {
  company_id: string;
  name: string;
  description?: string;
};

export type ProjectFromTemplateInput = Pick<
  ProjectCreateInput,
  "company_id" | "name" | "code" | "description" | "objective" | "status"
>;

export type ProjectFromTemplateResult = Project;
