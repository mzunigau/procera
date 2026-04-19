import { apiClient } from "../../shared/api/client";
import type {
  Task,
  TaskAttachment,
  TaskAttachmentCreateInput,
  TaskComment,
  TaskCommentCreateInput,
  TaskCreateInput,
  TaskStatus
} from "./types";

export function listTasks(projectId?: string) {
  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
  return apiClient.get<Task[]>(`/tasks${query}`);
}

export function createTask(input: TaskCreateInput) {
  return apiClient.post<Task>("/tasks", input);
}

export function updateTaskStatus(taskId: string, status: TaskStatus) {
  return apiClient.patch<Task>(`/tasks/${taskId}`, { status });
}

export function listTaskComments(taskId: string) {
  return apiClient.get<TaskComment[]>(`/tasks/${taskId}/comments`);
}

export function createTaskComment(taskId: string, input: TaskCommentCreateInput) {
  return apiClient.post<TaskComment>(`/tasks/${taskId}/comments`, input);
}

export function listTaskAttachments(taskId: string) {
  return apiClient.get<TaskAttachment[]>(`/tasks/${taskId}/attachments`);
}

export function createTaskAttachmentReference(taskId: string, input: TaskAttachmentCreateInput) {
  return apiClient.post<TaskAttachment>(`/tasks/${taskId}/attachments`, input);
}
