import { apiClient } from "../../shared/api/client";
import type { Process, ProcessCreateInput, ProcessStep, ProcessStepCreateInput } from "./types";

export function listProcesses() {
  return apiClient.get<Process[]>("/processes");
}

export function createProcess(input: ProcessCreateInput) {
  return apiClient.post<Process>("/processes", input);
}

export function listProcessSteps(processId?: string) {
  const query = processId ? `?process_id=${encodeURIComponent(processId)}` : "";
  return apiClient.get<ProcessStep[]>(`/process-steps${query}`);
}

export function createProcessStep(input: ProcessStepCreateInput) {
  return apiClient.post<ProcessStep>(`/processes/${input.process_id}/steps`, input);
}
