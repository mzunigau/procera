import { useCallback, useMemo } from "react";

import { StatusBadge } from "../../components/StatusBadge";
import { listProcesses } from "../processes/api";
import { listProjects } from "../projects/api";
import { listTasks } from "../tasks/api";
import type { Task, TaskStatus } from "../tasks/types";
import { useAsyncData } from "../../shared/hooks/useAsyncData";

const taskStatuses: TaskStatus[] = ["pending", "in_progress", "review", "completed", "blocked"];

type DashboardData = {
  projectCount: number;
  processCount: number;
  tasks: Task[];
};

function isOverdue(task: Task) {
  if (!task.due_date || task.status === "completed") {
    return false;
  }

  const dueDate = new Date(`${task.due_date}T00:00:00`);
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  return dueDate < today;
}

export function DashboardView() {
  const loadDashboard = useCallback(async (): Promise<DashboardData> => {
    const [projects, tasks, processes] = await Promise.all([
      listProjects(),
      listTasks(),
      listProcesses()
    ]);

    return {
      projectCount: projects.length,
      processCount: processes.filter((process) => process.status === "published").length,
      tasks
    };
  }, []);

  const { data, error, isLoading, reload } = useAsyncData(loadDashboard);

  const taskCounts = useMemo(() => {
    const counts = Object.fromEntries(taskStatuses.map((status) => [status, 0])) as Record<
      TaskStatus,
      number
    >;

    for (const task of data?.tasks ?? []) {
      counts[task.status] += 1;
    }

    return counts;
  }, [data?.tasks]);

  const overdueTasks = useMemo(() => (data?.tasks ?? []).filter(isOverdue), [data?.tasks]);
  const totalTasks = data?.tasks.length ?? 0;

  return (
    <section className="page-section">
      <div className="page-header">
        <div>
          <p className="eyebrow">Overview</p>
          <h1>Dashboard</h1>
        </div>
        <button className="secondary-button" onClick={() => void reload()} type="button">
          Refresh
        </button>
      </div>

      {error ? <div className="error-message">{error}</div> : null}

      <div className="dashboard-metrics">
        <div className="metric-tile">
          <span className="metric-label">Projects</span>
          <strong>{isLoading ? "-" : data?.projectCount ?? 0}</strong>
        </div>
        <div className="metric-tile">
          <span className="metric-label">Tasks</span>
          <strong>{isLoading ? "-" : totalTasks}</strong>
        </div>
        <div className="metric-tile">
          <span className="metric-label">Overdue tasks</span>
          <strong>{isLoading ? "-" : overdueTasks.length}</strong>
        </div>
        <div className="metric-tile">
          <span className="metric-label">Active processes</span>
          <strong>{isLoading ? "-" : data?.processCount ?? 0}</strong>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="panel">
          <div className="panel-heading">
            <h2>Tasks by status</h2>
          </div>
          <div className="status-summary">
            {taskStatuses.map((status) => (
              <div className="status-summary-row" key={status}>
                <StatusBadge value={status} />
                <strong>{isLoading ? "-" : taskCounts[status]}</strong>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="panel-heading">
            <h2>Overdue tasks</h2>
          </div>
          {isLoading ? (
            <p className="muted">Loading tasks...</p>
          ) : overdueTasks.length === 0 ? (
            <div className="empty-detail">No overdue tasks.</div>
          ) : (
            <div className="overdue-list">
              {overdueTasks.slice(0, 6).map((task) => (
                <div className="overdue-item" key={task.id}>
                  <div>
                    <strong>{task.title}</strong>
                    <span>Due {task.due_date}</span>
                  </div>
                  <StatusBadge value={task.status} />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
