import type {
  Document,
  DocumentLink,
  DocumentUploadInput,
  DocumentUploadResult,
  DocumentVersion,
  DocumentVersionUploadInput
} from "./types";

import { getRequestContextHeaders } from "../../shared/api/client";

const API_BASE_URL = "/api";

export async function listDocuments() {
  const response = await fetch(`${API_BASE_URL}/documents`, {
    headers: getRequestContextHeaders()
  });
  if (!response.ok) {
    throw await toError(response);
  }
  return response.json() as Promise<Document[]>;
}

export async function getDocument(documentId: string) {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
    headers: getRequestContextHeaders()
  });
  if (!response.ok) {
    throw await toError(response);
  }
  return response.json() as Promise<Document>;
}

export async function uploadDocument(input: DocumentUploadInput) {
  const formData = new FormData();
  formData.set("company_id", input.company_id);
  formData.set("title", input.title);
  formData.set("document_type", input.document_type);
  formData.set("file", input.file);

  setOptional(formData, "category", input.category);
  setOptional(formData, "owner_user_id", input.owner_user_id);
  setOptional(formData, "created_by_user_id", input.created_by_user_id);
  setOptional(formData, "change_summary", input.change_summary);
  setOptional(formData, "linked_type", input.linked_type);
  setOptional(formData, "linked_id", input.linked_id);
  setOptional(formData, "relation_type", input.relation_type);

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    body: formData,
    headers: getRequestContextHeaders(),
    method: "POST"
  });
  if (!response.ok) {
    throw await toError(response);
  }
  return response.json() as Promise<DocumentUploadResult>;
}

export async function listDocumentVersions(documentId: string) {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/versions`, {
    headers: getRequestContextHeaders()
  });
  if (!response.ok) {
    throw await toError(response);
  }
  return response.json() as Promise<DocumentVersion[]>;
}

export async function uploadDocumentVersion(documentId: string, input: DocumentVersionUploadInput) {
  const formData = new FormData();
  formData.set("company_id", input.company_id);
  formData.set("file", input.file);
  setOptional(formData, "created_by_user_id", input.created_by_user_id);
  setOptional(formData, "change_summary", input.change_summary);

  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/versions/upload`, {
    body: formData,
    headers: getRequestContextHeaders(),
    method: "POST"
  });
  if (!response.ok) {
    throw await toError(response);
  }
  return response.json() as Promise<DocumentVersion>;
}

export async function listDocumentLinks(documentId: string) {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/links`, {
    headers: getRequestContextHeaders()
  });
  if (!response.ok) {
    throw await toError(response);
  }
  return response.json() as Promise<DocumentLink[]>;
}

function setOptional(formData: FormData, key: string, value: string | undefined) {
  if (value) {
    formData.set(key, value);
  }
}

async function toError(response: Response) {
  try {
    const payload = await response.json();
    const message = typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail);
    return new Error(message);
  } catch {
    return new Error(`Request failed with status ${response.status}`);
  }
}
