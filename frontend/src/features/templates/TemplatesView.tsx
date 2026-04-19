import { useCallback, useMemo, useState } from "react";
import type { FormEvent } from "react";

import { DataTable } from "../../components/DataTable";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsyncData } from "../../shared/hooks/useAsyncData";
import { listProcesses } from "../processes/api";
import type { Process } from "../processes/types";
import { listProjects } from "../projects/api";
import type { Project, ProjectStatus } from "../projects/types";
import {
  createProjectFromTemplate,
  createTemplateFromProcess,
  createTemplateFromProject,
  listTemplates
} from "./api";
import type { Template, TemplateType } from "./types";

const projectStatuses: ProjectStatus[] = ["draft", "active", "on_hold", "completed", "cancelled", "archived"];

export function TemplatesView() {
  const templatesLoader = useCallback(() => listTemplates(), []);
  const projectsLoader = useCallback(() => listProjects(), []);
  const processesLoader = useCallback(() => listProcesses(), []);

  const { data: templates, error, isLoading, reload } = useAsyncData(templatesLoader);
  const { data: projects } = useAsyncData(projectsLoader);
  const { data: processes } = useAsyncData(processesLoader);
  const [sourceForm, setSourceForm] = useState({
    company_id: "company-1",
    description: "",
    name: "",
    source_id: "",
    template_type: "process" as Extract<TemplateType, "process" | "project">
  });
  const [projectForm, setProjectForm] = useState({
    code: "",
    company_id: "company-1",
    description: "",
    name: "",
    objective: "",
    status: "draft" as ProjectStatus,
    template_id: ""
  });
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitMessage, setSubmitMessage] = useState<string | null>(null);

  const sourceOptions = useMemo(() => {
    if (sourceForm.template_type === "process") {
      return (processes ?? []).map((process: Process) => ({ id: process.id, label: process.name }));
    }
    return (projects ?? []).map((project: Project) => ({ id: project.id, label: project.name }));
  }, [processes, projects, sourceForm.template_type]);

  async function handleCreateTemplate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitError(null);
    setSubmitMessage(null);
    try {
      const input = {
        company_id: sourceForm.company_id,
        description: sourceForm.description || undefined,
        name: sourceForm.name
      };
      if (sourceForm.template_type === "process") {
        await createTemplateFromProcess(sourceForm.source_id, input);
      } else {
        await createTemplateFromProject(sourceForm.source_id, input);
      }
      setSourceForm((current) => ({
        ...current,
        description: "",
        name: "",
        source_id: ""
      }));
      setSubmitMessage("Template created.");
      await reload();
    } catch (requestError) {
      setSubmitError(requestError instanceof Error ? requestError.message : "Unable to create template");
    }
  }

  async function handleCreateProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitError(null);
    setSubmitMessage(null);
    try {
      const project = await createProjectFromTemplate(projectForm.template_id, {
        code: projectForm.code || undefined,
        company_id: projectForm.company_id,
        description: projectForm.description || undefined,
        name: projectForm.name,
        objective: projectForm.objective || undefined,
        status: projectForm.status
      });
      setProjectForm((current) => ({
        ...current,
        code: "",
        description: "",
        name: "",
        objective: "",
        status: "draft",
        template_id: ""
      }));
      setSubmitMessage(`Project created: ${project.name}`);
    } catch (requestError) {
      setSubmitError(requestError instanceof Error ? requestError.message : "Unable to create project");
    }
  }

  return (
    <section className="page-section">
      <div className="page-header">
        <div>
          <p className="eyebrow">Reusable Structures</p>
          <h1>Templates</h1>
        </div>
      </div>

      <div className="content-grid">
        <div className="stack">
          <form className="panel form-panel" onSubmit={handleCreateTemplate}>
            <h2>Create Template</h2>
            <label>
              Company
              <input
                onChange={(event) => setSourceForm({ ...sourceForm, company_id: event.target.value })}
                required
                value={sourceForm.company_id}
              />
            </label>
            <label>
              Source Type
              <select
                onChange={(event) =>
                  setSourceForm({
                    ...sourceForm,
                    source_id: "",
                    template_type: event.target.value as Extract<TemplateType, "process" | "project">
                  })
                }
                value={sourceForm.template_type}
              >
                <option value="process">Process</option>
                <option value="project">Project</option>
              </select>
            </label>
            <label>
              Source
              <select
                onChange={(event) => setSourceForm({ ...sourceForm, source_id: event.target.value })}
                required
                value={sourceForm.source_id}
              >
                <option value="">Select source</option>
                {sourceOptions.map((source) => (
                  <option key={source.id} value={source.id}>
                    {source.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Template Name
              <input
                onChange={(event) => setSourceForm({ ...sourceForm, name: event.target.value })}
                required
                value={sourceForm.name}
              />
            </label>
            <label>
              Description
              <textarea
                onChange={(event) => setSourceForm({ ...sourceForm, description: event.target.value })}
                value={sourceForm.description}
              />
            </label>
            <button className="primary-button" type="submit">
              Create Template
            </button>
          </form>

          <form className="panel form-panel" onSubmit={handleCreateProject}>
            <h2>Create Project From Template</h2>
            <label>
              Template
              <select
                onChange={(event) => setProjectForm({ ...projectForm, template_id: event.target.value })}
                required
                value={projectForm.template_id}
              >
                <option value="">Select template</option>
                {(templates ?? [])
                  .filter((template) => template.template_type === "process" || template.template_type === "project")
                  .map((template) => (
                    <option key={template.id} value={template.id}>
                      {template.name}
                    </option>
                  ))}
              </select>
            </label>
            <label>
              Company
              <input
                onChange={(event) => setProjectForm({ ...projectForm, company_id: event.target.value })}
                required
                value={projectForm.company_id}
              />
            </label>
            <label>
              Project Name
              <input
                onChange={(event) => setProjectForm({ ...projectForm, name: event.target.value })}
                required
                value={projectForm.name}
              />
            </label>
            <div className="inline-fields">
              <label>
                Code
                <input onChange={(event) => setProjectForm({ ...projectForm, code: event.target.value })} value={projectForm.code} />
              </label>
              <label>
                Status
                <select
                  onChange={(event) => setProjectForm({ ...projectForm, status: event.target.value as ProjectStatus })}
                  value={projectForm.status}
                >
                  {projectStatuses.map((status) => (
                    <option key={status} value={status}>
                      {status.replaceAll("_", " ")}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <label>
              Objective
              <textarea
                onChange={(event) => setProjectForm({ ...projectForm, objective: event.target.value })}
                value={projectForm.objective}
              />
            </label>
            <label>
              Description
              <textarea
                onChange={(event) => setProjectForm({ ...projectForm, description: event.target.value })}
                value={projectForm.description}
              />
            </label>
            <button className="primary-button" type="submit">
              Create Project
            </button>
          </form>
        </div>

        <div className="panel list-panel">
          <div className="panel-heading">
            <h2>Template List</h2>
            {isLoading ? <span className="muted">Loading</span> : null}
          </div>
          {error ? <div className="error-message">{error}</div> : null}
          {submitError ? <div className="error-message">{submitError}</div> : null}
          {submitMessage ? <div className="success-message">{submitMessage}</div> : null}
          <DataTable<Template>
            columns={[
              { header: "Name", render: (template) => template.name },
              { header: "Type", render: (template) => <StatusBadge value={template.template_type} /> },
              { header: "Description", render: (template) => template.description ?? "" }
            ]}
            emptyMessage="No templates found"
            items={templates ?? []}
          />
        </div>
      </div>
    </section>
  );
}
