import { apiClient } from "../../shared/api/client";
import type {
  ProjectFromTemplateInput,
  ProjectFromTemplateResult,
  Template,
  TemplateFromSourceInput,
  TemplateType
} from "./types";

export function listTemplates(templateType?: TemplateType) {
  const query = templateType ? `?template_type=${encodeURIComponent(templateType)}` : "";
  return apiClient.get<Template[]>(`/templates${query}`);
}

export function createTemplateFromProcess(processId: string, input: TemplateFromSourceInput) {
  return apiClient.post<Template>(`/templates/from-process/${processId}`, input);
}

export function createTemplateFromProject(projectId: string, input: TemplateFromSourceInput) {
  return apiClient.post<Template>(`/templates/from-project/${projectId}`, input);
}

export function createProjectFromTemplate(templateId: string, input: ProjectFromTemplateInput) {
  return apiClient.post<ProjectFromTemplateResult>(`/templates/${templateId}/projects`, input);
}
