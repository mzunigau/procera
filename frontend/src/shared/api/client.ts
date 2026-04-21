export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number
  ) {
    super(message);
  }
}

const API_BASE_URL = "/api";
const DEFAULT_COMPANY_ID = "company-1";

export function getRequestContextHeaders() {
  const headers: Record<string, string> = {
    "X-Procera-Company-Id": DEFAULT_COMPANY_ID
  };

  if (typeof window !== "undefined") {
    const companyId = window.localStorage.getItem("procera_company_id");
    const userId = window.localStorage.getItem("procera_user_id");
    headers["X-Procera-Company-Id"] = companyId || DEFAULT_COMPANY_ID;
    if (userId) {
      headers["X-Procera-User-Id"] = userId;
    }
  }

  return headers;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...getRequestContextHeaders(),
      ...options.headers
    },
    ...options
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const payload = await response.json();
      message = typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail);
    } catch {
      // Keep fallback message.
    }
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const apiClient = {
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  get: <T>(path: string) => request<T>(path),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { body: JSON.stringify(body), method: "PATCH" }),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { body: JSON.stringify(body), method: "POST" })
};
