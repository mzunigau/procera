import { useCallback, useState } from "react";
import type { FormEvent } from "react";

import { DataTable } from "../../components/DataTable";
import { StatusBadge } from "../../components/StatusBadge";
import { listProcesses } from "../processes/api";
import type { Process } from "../processes/types";
import { createProject, listProjects } from "./api";
import { ProjectDetailView } from "./ProjectDetailView";
import type { Project, ProjectStatus } from "./types";
import { useAsyncData } from "../../shared/hooks/useAsyncData";

const projectStatuses: ProjectStatus[] = ["draft", "active", "on_hold", "completed", "cancelled", "archived"];

export function ProjectsView() {
  const projectsLoader = useCallback(() => listProjects(), []);
  const processesLoader = useCallback(() => listProcesses(), []);
  const { data: projects, error, isLoading, reload } = useAsyncData(projectsLoader);
  const { data: processes } = useAsyncData(processesLoader);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [form, setForm] = useState({
    code: "",
    company_id: "company-1",
    description: "",
    name: "",
    objective: "",
    process_id: "",
    status: "draft" as ProjectStatus
  });
  const [submitError, setSubmitError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitError(null);
    try {
      await createProject({
        code: form.code || undefined,
        company_id: form.company_id,
        description: form.description || undefined,
        name: form.name,
        objective: form.objective || undefined,
        process_id: form.process_id || undefined,
        status: form.status
      });
      setForm((current) => ({
        ...current,
        code: "",
        description: "",
        name: "",
        objective: "",
        process_id: "",
        status: "draft"
      }));
      await reload();
    } catch (requestError) {
      setSubmitError(requestError instanceof Error ? requestError.message : "Unable to create project");
    }
  }

  if (selectedProjectId) {
    return <ProjectDetailView onBack={() => setSelectedProjectId(null)} projectId={selectedProjectId} />;
  }

  return (
    <section className="page-section">
      <div className="page-header">
        <div>
          <p className="eyebrow">Project Execution</p>
          <h1>Projects</h1>
        </div>
      </div>

      <div className="content-grid">
        <form className="panel form-panel" onSubmit={handleSubmit}>
          <h2>Create Project</h2>
          <label>
            Company
            <input
              onChange={(event) => setForm({ ...form, company_id: event.target.value })}
              required
              value={form.company_id}
            />
          </label>
          <label>
            Name
            <input
              onChange={(event) => setForm({ ...form, name: event.target.value })}
              required
              value={form.name}
            />
          </label>
          <label>
            Code
            <input onChange={(event) => setForm({ ...form, code: event.target.value })} value={form.code} />
          </label>
          <label>
            Status
            <select
              onChange={(event) => setForm({ ...form, status: event.target.value as ProjectStatus })}
              value={form.status}
            >
              {projectStatuses.map((status) => (
                <option key={status} value={status}>
                  {status.replaceAll("_", " ")}
                </option>
              ))}
            </select>
          </label>
          <label>
            Process
            <select
              onChange={(event) => setForm({ ...form, process_id: event.target.value })}
              value={form.process_id}
            >
              <option value="">None</option>
              {(processes ?? []).map((process: Process) => (
                <option key={process.id} value={process.id}>
                  {process.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Objective
            <textarea
              onChange={(event) => setForm({ ...form, objective: event.target.value })}
              value={form.objective}
            />
          </label>
          <label>
            Description
            <textarea
              onChange={(event) => setForm({ ...form, description: event.target.value })}
              value={form.description}
            />
          </label>
          {submitError ? <div className="error-message">{submitError}</div> : null}
          <button className="primary-button" type="submit">
            Create Project
          </button>
        </form>

        <div className="panel list-panel">
          <div className="panel-heading">
            <h2>Project List</h2>
            {isLoading ? <span className="muted">Loading</span> : null}
          </div>
          {error ? <div className="error-message">{error}</div> : null}
          <DataTable<Project>
            columns={[
              { header: "Name", render: (project) => project.name },
              { header: "Code", render: (project) => project.code ?? "" },
              { header: "Status", render: (project) => <StatusBadge value={project.status} /> },
              { header: "Due Date", render: (project) => project.due_date ?? "" },
              {
                header: "Detail",
                render: (project) => (
                  <button className="small-button" onClick={() => setSelectedProjectId(project.id)} type="button">
                    Open
                  </button>
                )
              }
            ]}
            emptyMessage="No projects found"
            items={projects ?? []}
          />
        </div>
      </div>
    </section>
  );
}
