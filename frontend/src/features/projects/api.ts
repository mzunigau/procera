import { apiClient } from "../../shared/api/client";
import type { Project, ProjectCreateInput } from "./types";

export function listProjects() {
  return apiClient.get<Project[]>("/projects");
}

export function getProject(projectId: string) {
  return apiClient.get<Project>(`/projects/${projectId}`);
}

export function createProject(input: ProjectCreateInput) {
  return apiClient.post<Project>("/projects", input);
}
