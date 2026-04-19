import { StatusBadge } from "../../components/StatusBadge";
import type { Task, TaskStatus } from "./types";

type TasksKanbanViewProps = {
  onMoveTask: (taskId: string, status: TaskStatus) => Promise<void>;
  onSelectTask: (task: Task) => void;
  tasks: Task[];
};

export const taskStatuses: TaskStatus[] = ["pending", "in_progress", "review", "completed", "blocked"];

export function TasksKanbanView({ onMoveTask, onSelectTask, tasks }: TasksKanbanViewProps) {
  return (
    <div className="kanban-board">
      {taskStatuses.map((status) => {
        const columnTasks = tasks.filter((task) => task.status === status);
        return (
          <section className="kanban-column" key={status}>
            <div className="kanban-column-header">
              <StatusBadge value={status} />
              <span className="kanban-count">{columnTasks.length}</span>
            </div>

            <div className="kanban-cards">
              {columnTasks.length === 0 ? <div className="kanban-empty">No tasks</div> : null}
              {columnTasks.map((task) => (
                <article className="kanban-card" key={task.id}>
                  <div className="kanban-card-title">{task.title}</div>
                  {task.description ? <p>{task.description}</p> : null}
                  <div className="kanban-card-meta">
                    <span>{task.priority}</span>
                    {task.assigned_to ? <span>{`${task.assigned_to.type}: ${task.assigned_to.id}`}</span> : null}
                  </div>
                  <button className="small-button" onClick={() => onSelectTask(task)} type="button">
                    Open Details
                  </button>
                  <label>
                    Move To
                    <select
                      aria-label={`Move ${task.title}`}
                      onChange={(event) => void onMoveTask(task.id, event.target.value as TaskStatus)}
                      value={task.status}
                    >
                      {taskStatuses.map((nextStatus) => (
                        <option key={nextStatus} value={nextStatus}>
                          {nextStatus.replaceAll("_", " ")}
                        </option>
                      ))}
                    </select>
                  </label>
                </article>
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
