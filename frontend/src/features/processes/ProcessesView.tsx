import { useCallback, useState } from "react";
import type { FormEvent } from "react";

import { DataTable } from "../../components/DataTable";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsyncData } from "../../shared/hooks/useAsyncData";
import { createProcess, createProcessStep, listProcesses, listProcessSteps } from "./api";
import type { Process, ProcessStatus, ProcessStep } from "./types";

const processStatuses: ProcessStatus[] = ["draft", "published", "archived"];

export function ProcessesView() {
  const processesLoader = useCallback(() => listProcesses(), []);
  const stepsLoader = useCallback(() => listProcessSteps(), []);
  const { data: processes, error, isLoading, reload } = useAsyncData(processesLoader);
  const { data: steps, reload: reloadSteps } = useAsyncData(stepsLoader);
  const [processForm, setProcessForm] = useState({
    code: "",
    company_id: "company-1",
    name: "",
    objective: "",
    scope: "",
    status: "draft" as ProcessStatus,
    version_label: ""
  });
  const [stepForm, setStepForm] = useState({
    company_id: "company-1",
    description: "",
    name: "",
    process_id: "",
    requires_approval: false,
    requires_evidence: false,
    responsible_id: "",
    responsible_type: "user",
    step_order: 1
  });
  const [submitError, setSubmitError] = useState<string | null>(null);

  async function handleProcessSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitError(null);
    try {
      await createProcess({
        code: processForm.code || undefined,
        company_id: processForm.company_id,
        name: processForm.name,
        objective: processForm.objective || undefined,
        scope: processForm.scope || undefined,
        status: processForm.status,
        version_label: processForm.version_label || undefined
      });
      setProcessForm((current) => ({
        ...current,
        code: "",
        name: "",
        objective: "",
        scope: "",
        status: "draft",
        version_label: ""
      }));
      await reload();
    } catch (requestError) {
      setSubmitError(requestError instanceof Error ? requestError.message : "Unable to create process");
    }
  }

  async function handleStepSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitError(null);
    try {
      await createProcessStep({
        company_id: stepForm.company_id,
        description: stepForm.description || undefined,
        name: stepForm.name,
        process_id: stepForm.process_id,
        requires_approval: stepForm.requires_approval,
        requires_evidence: stepForm.requires_evidence,
        responsible_role_id:
          stepForm.responsible_type === "role" && stepForm.responsible_id ? stepForm.responsible_id : undefined,
        responsible_user_id:
          stepForm.responsible_type === "user" && stepForm.responsible_id ? stepForm.responsible_id : undefined,
        step_order: stepForm.step_order
      });
      setStepForm((current) => ({
        ...current,
        description: "",
        name: "",
        requires_approval: false,
        requires_evidence: false,
        responsible_id: "",
        step_order: current.step_order + 1
      }));
      await reloadSteps();
    } catch (requestError) {
      setSubmitError(requestError instanceof Error ? requestError.message : "Unable to create process step");
    }
  }

  return (
    <section className="page-section">
      <div className="page-header">
        <div>
          <p className="eyebrow">Process Definition</p>
          <h1>Processes</h1>
        </div>
      </div>

      <div className="content-grid">
        <div className="stack">
          <form className="panel form-panel" onSubmit={handleProcessSubmit}>
            <h2>Create Process</h2>
            <label>
              Company
              <input
                onChange={(event) => setProcessForm({ ...processForm, company_id: event.target.value })}
                required
                value={processForm.company_id}
              />
            </label>
            <label>
              Name
              <input
                onChange={(event) => setProcessForm({ ...processForm, name: event.target.value })}
                required
                value={processForm.name}
              />
            </label>
            <label>
              Code
              <input
                onChange={(event) => setProcessForm({ ...processForm, code: event.target.value })}
                value={processForm.code}
              />
            </label>
            <label>
              Status
              <select
                onChange={(event) => setProcessForm({ ...processForm, status: event.target.value as ProcessStatus })}
                value={processForm.status}
              >
                {processStatuses.map((status) => (
                  <option key={status} value={status}>
                    {status}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Objective
              <textarea
                onChange={(event) => setProcessForm({ ...processForm, objective: event.target.value })}
                value={processForm.objective}
              />
            </label>
            <label>
              Scope
              <textarea
                onChange={(event) => setProcessForm({ ...processForm, scope: event.target.value })}
                value={processForm.scope}
              />
            </label>
            <button className="primary-button" type="submit">
              Create Process
            </button>
          </form>

          <form className="panel form-panel" onSubmit={handleStepSubmit}>
            <h2>Add Step</h2>
            <label>
              Process
              <select
                onChange={(event) => setStepForm({ ...stepForm, process_id: event.target.value })}
                required
                value={stepForm.process_id}
              >
                <option value="">Select process</option>
                {(processes ?? []).map((process: Process) => (
                  <option key={process.id} value={process.id}>
                    {process.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Step Order
              <input
                min={1}
                onChange={(event) => setStepForm({ ...stepForm, step_order: Number(event.target.value) })}
                type="number"
                value={stepForm.step_order}
              />
            </label>
            <label>
              Name
              <input
                onChange={(event) => setStepForm({ ...stepForm, name: event.target.value })}
                required
                value={stepForm.name}
              />
            </label>
            <label>
              Description
              <textarea
                onChange={(event) => setStepForm({ ...stepForm, description: event.target.value })}
                value={stepForm.description}
              />
            </label>
            <div className="inline-fields">
              <label>
                Responsible Type
                <select
                  onChange={(event) => setStepForm({ ...stepForm, responsible_type: event.target.value })}
                  value={stepForm.responsible_type}
                >
                  <option value="user">User</option>
                  <option value="role">Role</option>
                </select>
              </label>
              <label>
                Responsible ID
                <input
                  onChange={(event) => setStepForm({ ...stepForm, responsible_id: event.target.value })}
                  value={stepForm.responsible_id}
                />
              </label>
            </div>
            <label className="checkbox-label">
              <input
                checked={stepForm.requires_evidence}
                onChange={(event) => setStepForm({ ...stepForm, requires_evidence: event.target.checked })}
                type="checkbox"
              />
              Requires Evidence
            </label>
            <label className="checkbox-label">
              <input
                checked={stepForm.requires_approval}
                onChange={(event) => setStepForm({ ...stepForm, requires_approval: event.target.checked })}
                type="checkbox"
              />
              Requires Approval
            </label>
            {submitError ? <div className="error-message">{submitError}</div> : null}
            <button className="primary-button" type="submit">
              Add Step
            </button>
          </form>
        </div>

        <div className="stack">
          <div className="panel list-panel">
            <div className="panel-heading">
              <h2>Process List</h2>
              {isLoading ? <span className="muted">Loading</span> : null}
            </div>
            {error ? <div className="error-message">{error}</div> : null}
            <DataTable<Process>
              columns={[
                { header: "Name", render: (process) => process.name },
                { header: "Code", render: (process) => process.code ?? "" },
                { header: "Status", render: (process) => <StatusBadge value={process.status} /> }
              ]}
              emptyMessage="No processes found"
              items={processes ?? []}
            />
          </div>

          <div className="panel list-panel">
            <div className="panel-heading">
              <h2>Process Steps</h2>
            </div>
            <DataTable<ProcessStep>
              columns={[
                { header: "Order", render: (step) => step.step_order },
                { header: "Name", render: (step) => step.name },
                {
                  header: "Responsible",
                  render: (step) => step.responsible_user_id ?? step.responsible_role_id ?? ""
                },
                { header: "Evidence", render: (step) => (step.requires_evidence ? "Yes" : "No") },
                { header: "Approval", render: (step) => (step.requires_approval ? "Yes" : "No") }
              ]}
              emptyMessage="No process steps found"
              items={steps ?? []}
            />
          </div>
        </div>
      </div>
    </section>
  );
}
