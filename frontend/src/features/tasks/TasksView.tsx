import { useCallback, useState } from "react";
import type { FormEvent } from "react";

import { DataTable } from "../../components/DataTable";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsyncData } from "../../shared/hooks/useAsyncData";
import { listProjects } from "../projects/api";
import type { Project } from "../projects/types";
import { createTask, listTasks, updateTaskStatus } from "./api";
import { TaskDetailPanel } from "./TaskDetailPanel";
import { taskStatuses, TasksKanbanView } from "./TasksKanbanView";
import type { AssignedTo, Task, TaskPriority, TaskStatus } from "./types";

const taskPriorities: TaskPriority[] = ["low", "medium", "high", "critical"];

export function TasksView() {
  const tasksLoader = useCallback(() => listTasks(), []);
  const projectsLoader = useCallback(() => listProjects(), []);
  const { data: tasks, error, isLoading, reload } = useAsyncData(tasksLoader);
  const { data: projects } = useAsyncData(projectsLoader);
  const [viewMode, setViewMode] = useState<"list" | "kanban">("kanban");
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [form, setForm] = useState({
    assignee_id: "",
    assignee_type: "user" as AssignedTo["type"],
    company_id: "company-1",
    description: "",
    priority: "medium" as TaskPriority,
    project_id: "",
    requires_approval: false,
    requires_evidence: false,
    status: "pending" as TaskStatus,
    title: ""
  });
  const [submitError, setSubmitError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitError(null);
    try {
      await createTask({
        assigned_to: form.assignee_id ? { type: form.assignee_type, id: form.assignee_id } : undefined,
        company_id: form.company_id,
        description: form.description || undefined,
        priority: form.priority,
        project_id: form.project_id,
        requires_approval: form.requires_approval,
        requires_evidence: form.requires_evidence,
        status: form.status,
        title: form.title
      });
      setForm((current) => ({
        ...current,
        assignee_id: "",
        description: "",
        priority: "medium",
        requires_approval: false,
        requires_evidence: false,
        status: "pending",
        title: ""
      }));
      await reload();
    } catch (requestError) {
      setSubmitError(requestError instanceof Error ? requestError.message : "Unable to create task");
    }
  }

  async function handleStatusChange(taskId: string, status: TaskStatus) {
    setSubmitError(null);
    try {
      await updateTaskStatus(taskId, status);
      await reload();
      setSelectedTask((current) => {
        if (!current || current.id !== taskId) {
          return current;
        }
        return { ...current, status };
      });
    } catch (requestError) {
      setSubmitError(requestError instanceof Error ? requestError.message : "Unable to update task");
    }
  }

  return (
    <section className="page-section">
      <div className="page-header">
        <div>
          <p className="eyebrow">Task Execution</p>
          <h1>Tasks</h1>
        </div>
        <div className="segmented-control" aria-label="Task view mode">
          <button
            className={viewMode === "kanban" ? "active" : ""}
            onClick={() => setViewMode("kanban")}
            type="button"
          >
            Kanban
          </button>
          <button
            className={viewMode === "list" ? "active" : ""}
            onClick={() => setViewMode("list")}
            type="button"
          >
            List
          </button>
        </div>
      </div>

      <div className={selectedTask ? "task-workspace with-detail" : "task-workspace"}>
        <form className="panel form-panel" onSubmit={handleSubmit}>
          <h2>Create Task</h2>
          <label>
            Company
            <input
              onChange={(event) => setForm({ ...form, company_id: event.target.value })}
              required
              value={form.company_id}
            />
          </label>
          <label>
            Project
            <select
              onChange={(event) => setForm({ ...form, project_id: event.target.value })}
              required
              value={form.project_id}
            >
              <option value="">Select project</option>
              {(projects ?? []).map((project: Project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Title
            <input
              onChange={(event) => setForm({ ...form, title: event.target.value })}
              required
              value={form.title}
            />
          </label>
          <label>
            Description
            <textarea
              onChange={(event) => setForm({ ...form, description: event.target.value })}
              value={form.description}
            />
          </label>
          <label>
            Status
            <select
              onChange={(event) => setForm({ ...form, status: event.target.value as TaskStatus })}
              value={form.status}
            >
              {taskStatuses.map((status) => (
                <option key={status} value={status}>
                  {status.replaceAll("_", " ")}
                </option>
              ))}
            </select>
          </label>
          <label>
            Priority
            <select
              onChange={(event) => setForm({ ...form, priority: event.target.value as TaskPriority })}
              value={form.priority}
            >
              {taskPriorities.map((priority) => (
                <option key={priority} value={priority}>
                  {priority}
                </option>
              ))}
            </select>
          </label>
          <div className="inline-fields">
            <label>
              Responsible Type
              <select
                onChange={(event) =>
                  setForm({ ...form, assignee_type: event.target.value as AssignedTo["type"] })
                }
                value={form.assignee_type}
              >
                <option value="user">User</option>
                <option value="role">Role</option>
              </select>
            </label>
            <label>
              Responsible ID
              <input
                onChange={(event) => setForm({ ...form, assignee_id: event.target.value })}
                value={form.assignee_id}
              />
            </label>
          </div>
          <label className="checkbox-label">
            <input
              checked={form.requires_evidence}
              onChange={(event) => setForm({ ...form, requires_evidence: event.target.checked })}
              type="checkbox"
            />
            Requires Evidence
          </label>
          <label className="checkbox-label">
            <input
              checked={form.requires_approval}
              onChange={(event) => setForm({ ...form, requires_approval: event.target.checked })}
              type="checkbox"
            />
            Requires Approval
          </label>
          {submitError ? <div className="error-message">{submitError}</div> : null}
          <button className="primary-button" type="submit">
            Create Task
          </button>
        </form>

        <div className="panel list-panel">
          <div className="panel-heading">
            <h2>{viewMode === "kanban" ? "Task Board" : "Task List"}</h2>
            {isLoading ? <span className="muted">Loading</span> : null}
          </div>
          {error ? <div className="error-message">{error}</div> : null}
          {viewMode === "kanban" ? (
            <TasksKanbanView onMoveTask={handleStatusChange} onSelectTask={setSelectedTask} tasks={tasks ?? []} />
          ) : (
            <DataTable<Task>
              columns={[
                { header: "Title", render: (task) => task.title },
                { header: "Status", render: (task) => <StatusBadge value={task.status} /> },
                { header: "Priority", render: (task) => task.priority },
                {
                  header: "Responsible",
                  render: (task) => (task.assigned_to ? `${task.assigned_to.type}: ${task.assigned_to.id}` : "")
                },
                {
                  header: "Detail",
                  render: (task) => (
                    <button className="small-button" onClick={() => setSelectedTask(task)} type="button">
                      Open
                    </button>
                  )
                },
                {
                  header: "Move",
                  render: (task) => (
                    <select
                      aria-label={`Update ${task.title} status`}
                      onChange={(event) => void handleStatusChange(task.id, event.target.value as TaskStatus)}
                      value={task.status}
                    >
                      {taskStatuses.map((status) => (
                        <option key={status} value={status}>
                          {status.replaceAll("_", " ")}
                        </option>
                      ))}
                    </select>
                  )
                }
              ]}
              emptyMessage="No tasks found"
              items={tasks ?? []}
            />
          )}
        </div>

        {selectedTask ? (
          <TaskDetailPanel
            onClose={() => setSelectedTask(null)}
            task={(tasks ?? []).find((task) => task.id === selectedTask.id) ?? selectedTask}
          />
        ) : null}
      </div>
    </section>
  );
}
