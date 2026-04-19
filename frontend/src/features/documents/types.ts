export type DocumentStatus = "draft" | "in_review" | "approved" | "obsolete";
export type DocumentVersionStatus = "draft" | "in_review" | "approved" | "rejected" | "obsolete";
export type DocumentLinkedType = "process" | "process_step" | "task";

export type Document = {
  id: string;
  company_id: string;
  title: string;
  document_type: string;
  category: string | null;
  current_version_id: string | null;
  owner_user_id: string | null;
  status: DocumentStatus;
  created_at: string;
  updated_at: string;
};

export type DocumentVersion = {
  id: string;
  company_id: string;
  document_id: string;
  version_number: number;
  file_name: string;
  storage_key: string;
  content_type: string | null;
  size_bytes: number;
  change_summary: string | null;
  status: DocumentVersionStatus;
  created_by_user_id: string | null;
  approved_by_user_id: string | null;
  approved_at: string | null;
  created_at: string;
};

export type DocumentLink = {
  id: string;
  company_id: string;
  document_id: string;
  linked_type: DocumentLinkedType;
  linked_id: string;
  relation_type: string;
  created_at: string;
};

export type DocumentUploadResult = {
  document: Document;
  version: DocumentVersion;
  link: DocumentLink | null;
};

export type DocumentUploadInput = {
  category?: string;
  change_summary?: string;
  company_id: string;
  created_by_user_id?: string;
  document_type: string;
  file: File;
  linked_id?: string;
  linked_type?: DocumentLinkedType;
  owner_user_id?: string;
  relation_type?: string;
  title: string;
};

export type DocumentVersionUploadInput = {
  change_summary?: string;
  company_id: string;
  created_by_user_id?: string;
  file: File;
};
