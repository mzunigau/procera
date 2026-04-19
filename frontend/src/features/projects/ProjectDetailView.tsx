import { useCallback, useMemo } from "react";

import { DataTable } from "../../components/DataTable";
import { StatusBadge } from "../../components/StatusBadge";
import { listProcesses, listProcessSteps } from "../processes/api";
import type { Process, ProcessStep } from "../processes/types";
import { listTasks } from "../tasks/api";
import type { Task } from "../tasks/types";
import { useAsyncData } from "../../shared/hooks/useAsyncData";
import { getProject } from "./api";

type ProjectDetailViewProps = {
  projectId: string;
  onBack: () => void;
};

export function ProjectDetailView({ projectId, onBack }: ProjectDetailViewProps) {
  const projectLoader = useCallback(() => getProject(projectId), [projectId]);
  const tasksLoader = useCallback(() => listTasks(projectId), [projectId]);
  const stepsLoader = useCallback(() => listProcessSteps(), []);
  const processesLoader = useCallback(() => listProcesses(), []);

  const { data: project, error: projectError, isLoading: isProjectLoading } = useAsyncData(projectLoader);
  const { data: tasks, error: tasksError, isLoading: areTasksLoading } = useAsyncData(tasksLoader);
  const { data: processSteps } = useAsyncData(stepsLoader);
  const { data: processes } = useAsyncData(processesLoader);

  const relatedProcesses = useMemo(() => {
    const processStepIds = new Set((tasks ?? []).map((task) => task.process_step_id).filter(Boolean));
    const processIds = new Set(
      (processSteps ?? [])
        .filter((step: ProcessStep) => processStepIds.has(step.id))
        .map((step: ProcessStep) => step.process_id)
    );

    return (processes ?? []).filter((process: Process) => processIds.has(process.id));
  }, [processes, processSteps, tasks]);

  return (
    <section className="page-section">
      <div className="page-header">
        <div>
          <p className="eyebrow">Project Detail</p>
          <h1>{project?.name ?? "Project"}</h1>
        </div>
        <button className="secondary-button" onClick={onBack} type="button">
          Back to Projects
        </button>
      </div>

      {projectError ? <div className="error-message">{projectError}</div> : null}

      <div className="detail-grid">
        <div className="panel">
          <div className="panel-heading">
            <h2>General Information</h2>
            {isProjectLoading ? <span className="muted">Loading</span> : null}
          </div>
          {project ? (
            <dl className="detail-list">
              <div>
                <dt>Company</dt>
                <dd>{project.company_id}</dd>
              </div>
              <div>
                <dt>Code</dt>
                <dd>{project.code ?? ""}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>
                  <StatusBadge value={project.status} />
                </dd>
              </div>
              <div>
                <dt>Owner</dt>
                <dd>{project.owner_user_id ?? ""}</dd>
              </div>
              <div>
                <dt>Start Date</dt>
                <dd>{project.start_date ?? ""}</dd>
              </div>
              <div>
                <dt>Due Date</dt>
                <dd>{project.due_date ?? ""}</dd>
              </div>
              <div className="wide-detail">
                <dt>Objective</dt>
                <dd>{project.objective ?? ""}</dd>
              </div>
              <div className="wide-detail">
                <dt>Description</dt>
                <dd>{project.description ?? ""}</dd>
              </div>
            </dl>
          ) : null}
        </div>

        <div className="panel">
          <div className="panel-heading">
            <h2>Related Process</h2>
          </div>
          {relatedProcesses.length > 0 ? (
            <DataTable<Process>
              columns={[
                { header: "Name", render: (process) => process.name },
                { header: "Code", render: (process) => process.code ?? "" },
                { header: "Status", render: (process) => <StatusBadge value={process.status} /> }
              ]}
              emptyMessage="No related process found"
              items={relatedProcesses}
            />
          ) : (
            <div className="empty-detail">No related process found</div>
          )}
        </div>
      </div>

      <div className="panel list-panel">
        <div className="panel-heading">
          <h2>Associated Tasks</h2>
          {areTasksLoading ? <span className="muted">Loading</span> : null}
        </div>
        {tasksError ? <div className="error-message">{tasksError}</div> : null}
        <DataTable<Task>
          columns={[
            { header: "Title", render: (task) => task.title },
            { header: "Status", render: (task) => <StatusBadge value={task.status} /> },
            { header: "Priority", render: (task) => task.priority },
            {
              header: "Responsible",
              render: (task) => (task.assigned_to ? `${task.assigned_to.type}: ${task.assigned_to.id}` : "")
            },
            { header: "Evidence", render: (task) => (task.requires_evidence ? "Yes" : "No") },
            { header: "Approval", render: (task) => (task.requires_approval ? "Yes" : "No") }
          ]}
          emptyMessage="No tasks associated with this project"
          items={tasks ?? []}
        />
      </div>
    </section>
  );
}
