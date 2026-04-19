import { useCallback, useMemo, useState } from "react";
import type { FormEvent } from "react";

import { DataTable } from "../../components/DataTable";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsyncData } from "../../shared/hooks/useAsyncData";
import { listProcesses } from "../processes/api";
import type { Process, ProcessStep } from "../processes/types";
import { listProcessSteps } from "../processes/api";
import { listTasks } from "../tasks/api";
import type { Task } from "../tasks/types";
import {
  listDocumentLinks,
  listDocuments,
  listDocumentVersions,
  uploadDocument,
  uploadDocumentVersion
} from "./api";
import type { Document, DocumentLinkedType, DocumentLink, DocumentVersion } from "./types";

export function DocumentsView() {
  const documentsLoader = useCallback(() => listDocuments(), []);
  const processesLoader = useCallback(() => listProcesses(), []);
  const processStepsLoader = useCallback(() => listProcessSteps(), []);
  const tasksLoader = useCallback(() => listTasks(), []);

  const { data: documents, error, isLoading, reload } = useAsyncData(documentsLoader);
  const { data: processes } = useAsyncData(processesLoader);
  const { data: processSteps } = useAsyncData(processStepsLoader);
  const { data: tasks } = useAsyncData(tasksLoader);

  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [form, setForm] = useState({
    category: "",
    change_summary: "",
    company_id: "company-1",
    created_by_user_id: "",
    document_type: "procedure",
    linked_id: "",
    linked_type: "process" as DocumentLinkedType,
    owner_user_id: "",
    relation_type: "reference",
    title: ""
  });
  const [file, setFile] = useState<File | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const linkTargets = useMemo(() => {
    if (form.linked_type === "process") {
      return (processes ?? []).map((process: Process) => ({ id: process.id, label: process.name }));
    }
    if (form.linked_type === "process_step") {
      return (processSteps ?? []).map((step: ProcessStep) => ({ id: step.id, label: step.name }));
    }
    return (tasks ?? []).map((task: Task) => ({ id: task.id, label: task.title }));
  }, [form.linked_type, processes, processSteps, tasks]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitError(null);
    if (!file) {
      setSubmitError("Select a file to upload");
      return;
    }

    try {
      await uploadDocument({
        category: form.category || undefined,
        change_summary: form.change_summary || undefined,
        company_id: form.company_id,
        created_by_user_id: form.created_by_user_id || undefined,
        document_type: form.document_type,
        file,
        linked_id: form.linked_id || undefined,
        linked_type: form.linked_id ? form.linked_type : undefined,
        owner_user_id: form.owner_user_id || undefined,
        relation_type: form.linked_id ? form.relation_type : undefined,
        title: form.title
      });
      setForm((current) => ({
        ...current,
        category: "",
        change_summary: "",
        created_by_user_id: "",
        linked_id: "",
        owner_user_id: "",
        title: ""
      }));
      setFile(null);
      await reload();
    } catch (requestError) {
      setSubmitError(requestError instanceof Error ? requestError.message : "Unable to upload document");
    }
  }

  return (
    <section className="page-section">
      <div className="page-header">
        <div>
          <p className="eyebrow">Document Control</p>
          <h1>Documents</h1>
        </div>
      </div>

      <div className={selectedDocument ? "task-workspace with-detail" : "content-grid"}>
        <form className="panel form-panel" onSubmit={handleSubmit}>
          <h2>Upload Document</h2>
          <label>
            Company
            <input
              onChange={(event) => setForm({ ...form, company_id: event.target.value })}
              required
              value={form.company_id}
            />
          </label>
          <label>
            Title
            <input onChange={(event) => setForm({ ...form, title: event.target.value })} required value={form.title} />
          </label>
          <label>
            Document Type
            <select
              onChange={(event) => setForm({ ...form, document_type: event.target.value })}
              value={form.document_type}
            >
              <option value="policy">policy</option>
              <option value="procedure">procedure</option>
              <option value="manual">manual</option>
              <option value="template">template</option>
              <option value="record">record</option>
              <option value="form">form</option>
            </select>
          </label>
          <label>
            Category
            <input onChange={(event) => setForm({ ...form, category: event.target.value })} value={form.category} />
          </label>
          <label>
            File
            <input
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              required
              type="file"
            />
          </label>
          <label>
            Link Target Type
            <select
              onChange={(event) =>
                setForm({ ...form, linked_id: "", linked_type: event.target.value as DocumentLinkedType })
              }
              value={form.linked_type}
            >
              <option value="process">Process</option>
              <option value="process_step">Process Step</option>
              <option value="task">Task</option>
            </select>
          </label>
          <label>
            Link Target
            <select onChange={(event) => setForm({ ...form, linked_id: event.target.value })} value={form.linked_id}>
              <option value="">None</option>
              {linkTargets.map((target) => (
                <option key={target.id} value={target.id}>
                  {target.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Relation Type
            <input
              onChange={(event) => setForm({ ...form, relation_type: event.target.value })}
              value={form.relation_type}
            />
          </label>
          <label>
            Change Summary
            <textarea
              onChange={(event) => setForm({ ...form, change_summary: event.target.value })}
              value={form.change_summary}
            />
          </label>
          {submitError ? <div className="error-message">{submitError}</div> : null}
          <button className="primary-button" type="submit">
            Upload Document
          </button>
        </form>

        <div className="panel list-panel">
          <div className="panel-heading">
            <h2>Document List</h2>
            {isLoading ? <span className="muted">Loading</span> : null}
          </div>
          {error ? <div className="error-message">{error}</div> : null}
          <DataTable<Document>
            columns={[
              { header: "Title", render: (document) => document.title },
              { header: "Type", render: (document) => document.document_type },
              { header: "Status", render: (document) => <StatusBadge value={document.status} /> },
              { header: "Category", render: (document) => document.category ?? "" },
              {
                header: "Detail",
                render: (document) => (
                  <button className="small-button" onClick={() => setSelectedDocument(document)} type="button">
                    Open
                  </button>
                )
              }
            ]}
            emptyMessage="No documents found"
            items={documents ?? []}
          />
        </div>

        {selectedDocument ? (
          <DocumentDetailPanel document={selectedDocument} onClose={() => setSelectedDocument(null)} />
        ) : null}
      </div>
    </section>
  );
}

function DocumentDetailPanel({ document, onClose }: { document: Document; onClose: () => void }) {
  const versionsLoader = useCallback(() => listDocumentVersions(document.id), [document.id]);
  const linksLoader = useCallback(() => listDocumentLinks(document.id), [document.id]);
  const { data: versions, reload: reloadVersions } = useAsyncData(versionsLoader);
  const { data: links } = useAsyncData(linksLoader);
  const [versionFile, setVersionFile] = useState<File | null>(null);
  const [versionForm, setVersionForm] = useState({
    change_summary: "",
    created_by_user_id: ""
  });
  const [versionError, setVersionError] = useState<string | null>(null);

  async function handleVersionSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setVersionError(null);
    if (!versionFile) {
      setVersionError("Select a file for the new version");
      return;
    }

    try {
      await uploadDocumentVersion(document.id, {
        change_summary: versionForm.change_summary || undefined,
        company_id: document.company_id,
        created_by_user_id: versionForm.created_by_user_id || undefined,
        file: versionFile
      });
      setVersionFile(null);
      setVersionForm({ change_summary: "", created_by_user_id: "" });
      await reloadVersions();
    } catch (requestError) {
      setVersionError(requestError instanceof Error ? requestError.message : "Unable to upload version");
    }
  }

  return (
    <aside className="task-detail-panel">
      <div className="panel-heading">
        <div>
          <h2>{document.title}</h2>
          <div className="task-detail-meta">
            <StatusBadge value={document.status} />
            <span>{document.document_type}</span>
          </div>
        </div>
        <button className="small-button" onClick={onClose} type="button">
          Close
        </button>
      </div>

      <div className="task-detail-section">
        <h3>General Information</h3>
        <dl className="compact-detail-list">
          <div>
            <dt>Company</dt>
            <dd>{document.company_id}</dd>
          </div>
          <div>
            <dt>Category</dt>
            <dd>{document.category ?? ""}</dd>
          </div>
          <div>
            <dt>Current Version</dt>
            <dd>{document.current_version_id ?? ""}</dd>
          </div>
          <div>
            <dt>Owner</dt>
            <dd>{document.owner_user_id ?? ""}</dd>
          </div>
        </dl>
      </div>

      <div className="task-detail-section">
        <h3>Versions</h3>
        <form className="inline-form" onSubmit={handleVersionSubmit}>
          <label>
            New Version File
            <input onChange={(event) => setVersionFile(event.target.files?.[0] ?? null)} required type="file" />
          </label>
          <label>
            Change Summary
            <textarea
              onChange={(event) => setVersionForm({ ...versionForm, change_summary: event.target.value })}
              value={versionForm.change_summary}
            />
          </label>
          <label>
            Created By User ID
            <input
              onChange={(event) => setVersionForm({ ...versionForm, created_by_user_id: event.target.value })}
              value={versionForm.created_by_user_id}
            />
          </label>
          {versionError ? <div className="error-message">{versionError}</div> : null}
          <button className="primary-button" type="submit">
            Upload New Version
          </button>
        </form>
        <div className="attachment-list">
          {(versions ?? []).map((version: DocumentVersion) => (
            <div className="attachment-item" key={version.id}>
              <strong>{`v${version.version_number} - ${version.file_name}`}</strong>
              <span>{version.storage_key}</span>
              <span>{version.change_summary ?? ""}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="task-detail-section">
        <h3>Links</h3>
        <div className="attachment-list">
          {(links ?? []).map((link: DocumentLink) => (
            <div className="attachment-item" key={link.id}>
              <strong>{`${link.linked_type}: ${link.linked_id}`}</strong>
              <span>{link.relation_type}</span>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}
