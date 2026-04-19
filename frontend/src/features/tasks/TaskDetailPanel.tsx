import { useCallback, useMemo, useState } from "react";
import type { FormEvent } from "react";

import { StatusBadge } from "../../components/StatusBadge";
import { listAuditLogs } from "../audit/api";
import type { AuditLog } from "../audit/types";
import { createTaskAttachmentReference, createTaskComment, listTaskAttachments, listTaskComments } from "./api";
import type { Task, TaskAttachment, TaskComment } from "./types";
import { useAsyncData } from "../../shared/hooks/useAsyncData";

type TaskDetailPanelProps = {
  onClose: () => void;
  task: Task;
};

export function TaskDetailPanel({ onClose, task }: TaskDetailPanelProps) {
  const commentsLoader = useCallback(() => listTaskComments(task.id), [task.id]);
  const attachmentsLoader = useCallback(() => listTaskAttachments(task.id), [task.id]);
  const auditLoader = useCallback(() => listAuditLogs({ target_id: task.id, target_type: "task" }), [task.id]);

  const { data: comments, reload: reloadComments } = useAsyncData(commentsLoader);
  const { data: attachments, reload: reloadAttachments } = useAsyncData(attachmentsLoader);
  const { data: auditLogs } = useAsyncData(auditLoader);

  const [commentForm, setCommentForm] = useState({
    author_user_id: "",
    body: ""
  });
  const [attachmentForm, setAttachmentForm] = useState({
    content_type: "",
    file_name: "",
    size_bytes: 0,
    storage_key: "",
    uploaded_by_user_id: ""
  });
  const [panelError, setPanelError] = useState<string | null>(null);

  const activityItems = useMemo(() => {
    const commentItems = (comments ?? []).map((comment: TaskComment) => ({
      at: comment.created_at,
      id: `comment-${comment.id}`,
      label: "Comment",
      text: comment.body
    }));
    const attachmentItems = (attachments ?? []).map((attachment: TaskAttachment) => ({
      at: attachment.created_at,
      id: `attachment-${attachment.id}`,
      label: "Attachment",
      text: attachment.file_name
    }));
    const auditItems = (auditLogs ?? []).map((auditLog: AuditLog) => ({
      at: auditLog.created_at,
      id: `audit-${auditLog.id}`,
      label: auditLog.action,
      text: auditLog.summary
    }));

    return [...commentItems, ...attachmentItems, ...auditItems].sort((left, right) =>
      left.at.localeCompare(right.at)
    );
  }, [attachments, auditLogs, comments]);

  async function handleCommentSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPanelError(null);
    try {
      await createTaskComment(task.id, {
        author_user_id: commentForm.author_user_id || undefined,
        body: commentForm.body,
        company_id: task.company_id
      });
      setCommentForm({ author_user_id: "", body: "" });
      await reloadComments();
    } catch (requestError) {
      setPanelError(requestError instanceof Error ? requestError.message : "Unable to add comment");
    }
  }

  async function handleAttachmentSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPanelError(null);
    try {
      await createTaskAttachmentReference(task.id, {
        company_id: task.company_id,
        content_type: attachmentForm.content_type || undefined,
        file_name: attachmentForm.file_name,
        size_bytes: attachmentForm.size_bytes,
        storage_key: attachmentForm.storage_key,
        uploaded_by_user_id: attachmentForm.uploaded_by_user_id || undefined
      });
      setAttachmentForm({
        content_type: "",
        file_name: "",
        size_bytes: 0,
        storage_key: "",
        uploaded_by_user_id: ""
      });
      await reloadAttachments();
    } catch (requestError) {
      setPanelError(requestError instanceof Error ? requestError.message : "Unable to add attachment");
    }
  }

  return (
    <aside className="task-detail-panel">
      <div className="panel-heading">
        <div>
          <h2>{task.title}</h2>
          <div className="task-detail-meta">
            <StatusBadge value={task.status} />
            <span>{task.priority}</span>
          </div>
        </div>
        <button className="small-button" onClick={onClose} type="button">
          Close
        </button>
      </div>

      {panelError ? <div className="error-message">{panelError}</div> : null}

      <div className="task-detail-section">
        <h3>Task Information</h3>
        <dl className="compact-detail-list">
          <div>
            <dt>Project</dt>
            <dd>{task.project_id}</dd>
          </div>
          <div>
            <dt>Responsible</dt>
            <dd>{task.assigned_to ? `${task.assigned_to.type}: ${task.assigned_to.id}` : ""}</dd>
          </div>
          <div>
            <dt>Evidence</dt>
            <dd>{task.requires_evidence ? "Required" : "Not required"}</dd>
          </div>
          <div>
            <dt>Approval</dt>
            <dd>{task.requires_approval ? "Required" : "Not required"}</dd>
          </div>
        </dl>
        {task.description ? <p className="task-description">{task.description}</p> : null}
      </div>

      <form className="task-detail-section" onSubmit={handleCommentSubmit}>
        <h3>Comments</h3>
        <label>
          Author User ID
          <input
            onChange={(event) => setCommentForm({ ...commentForm, author_user_id: event.target.value })}
            value={commentForm.author_user_id}
          />
        </label>
        <label>
          Comment
          <textarea
            onChange={(event) => setCommentForm({ ...commentForm, body: event.target.value })}
            required
            value={commentForm.body}
          />
        </label>
        <button className="primary-button" type="submit">
          Add Comment
        </button>
        <div className="timeline-list">
          {(comments ?? []).map((comment) => (
            <div className="timeline-item" key={comment.id}>
              <div className="timeline-meta">{formatDateTime(comment.created_at)}</div>
              <div>{comment.body}</div>
            </div>
          ))}
        </div>
      </form>

      <form className="task-detail-section" onSubmit={handleAttachmentSubmit}>
        <h3>Attachments</h3>
        <label>
          File Name
          <input
            onChange={(event) => setAttachmentForm({ ...attachmentForm, file_name: event.target.value })}
            required
            value={attachmentForm.file_name}
          />
        </label>
        <label>
          Reference
          <input
            onChange={(event) => setAttachmentForm({ ...attachmentForm, storage_key: event.target.value })}
            required
            value={attachmentForm.storage_key}
          />
        </label>
        <div className="inline-fields">
          <label>
            Content Type
            <input
              onChange={(event) => setAttachmentForm({ ...attachmentForm, content_type: event.target.value })}
              value={attachmentForm.content_type}
            />
          </label>
          <label>
            Size Bytes
            <input
              min={0}
              onChange={(event) => setAttachmentForm({ ...attachmentForm, size_bytes: Number(event.target.value) })}
              type="number"
              value={attachmentForm.size_bytes}
            />
          </label>
        </div>
        <label>
          Uploaded By User ID
          <input
            onChange={(event) => setAttachmentForm({ ...attachmentForm, uploaded_by_user_id: event.target.value })}
            value={attachmentForm.uploaded_by_user_id}
          />
        </label>
        <button className="primary-button" type="submit">
          Add Attachment
        </button>
        <div className="attachment-list">
          {(attachments ?? []).map((attachment) => (
            <div className="attachment-item" key={attachment.id}>
              <strong>{attachment.file_name}</strong>
              <span>{attachment.storage_key}</span>
            </div>
          ))}
        </div>
      </form>

      <div className="task-detail-section">
        <h3>Activity</h3>
        <div className="timeline-list">
          {activityItems.length === 0 ? <div className="empty-detail">No activity found</div> : null}
          {activityItems.map((item) => (
            <div className="timeline-item" key={item.id}>
              <div className="timeline-meta">
                {formatDateTime(item.at)} · {item.label}
              </div>
              <div>{item.text}</div>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}
