import axios from "axios";
import type {
  AuthToken,
  LoginPayload,
  RegisterPayload,
  InvitePayload,
  InviteResponse,
  OnboardingProgress,
  OnboardingStep,
  SupportTicket,
  TeamProgressResponse,
  UnreadCountResponse,
  PendingUpdate,
  FeedbackPayload,
  ConversationHistoryResponse,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "true",
  },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("vf_access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-logout on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      // Prevent infinite redirect or clearing state when already trying to log in
      if (err.config?.url !== "/api/v1/auth/login") {
        localStorage.removeItem("vf_access_token");
        localStorage.removeItem("vf_user");
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  }
);

// ---------------------------------------------------------------------------
// Auth API
// ---------------------------------------------------------------------------

export const authApi = {
  register: (payload: RegisterPayload) =>
    api.post<AuthToken>("/api/v1/auth/register", payload).then((r) => r.data),

  login: (payload: LoginPayload) =>
    api.post<AuthToken>("/api/v1/auth/login", payload).then((r) => r.data),

  me: () =>
    api.get("/api/v1/auth/me").then((r) => r.data),

  invite: (payload: InvitePayload) =>
    api.post<InviteResponse>("/api/v1/auth/invite", payload).then((r) => r.data),

  acceptInvite: (payload: { token: string; full_name: string; password: string }) =>
    api.post<AuthToken>("/api/v1/auth/invite/accept", payload).then((r) => r.data),
};

// ---------------------------------------------------------------------------
// Onboarding API
// ---------------------------------------------------------------------------

export const onboardingApi = {
  getSteps: () =>
    api.get<OnboardingStep[]>("/api/v1/auth/onboarding/steps").then((r) => r.data),

  getProgress: () =>
    api.get<OnboardingProgress>("/api/v1/auth/onboarding/progress").then((r) => r.data),

  completeStep: (stepId: number) =>
    api
      .post<OnboardingProgress>(`/api/v1/auth/onboarding/steps/${stepId}/complete`)
      .then((r) => r.data),

  completeSection: (sectionId: string) =>
    api.post<OnboardingProgress>(`/api/v1/auth/onboarding/sections/${sectionId}/complete`)
      .then((r) => r.data),

  submitQuiz: (moduleId: number, score: number) =>
    api.post(`/api/v1/auth/onboarding/quizzes/submit`, {
      module_id: moduleId,
      score,
    }).then((r) => r.data),
};

/**
 * URL tới một tài liệu onboarding thật trong data/raw hoặc MinIO.
 *
 * Thẻ <video>/<iframe> không gửi được header Authorization, nên JWT được đính
 * kèm qua query `?token=` — backend chấp nhận cả hai cách.
 */
export const mediaUrl = (path: string, download = false): string => {
  const token = localStorage.getItem("vf_access_token") ?? "";
  const params = new URLSearchParams({ token });
  if (download) params.set("download", "1");

  // Nếu path là link MinIO (chứa s3:// hoặc :9000/vinfast-onboarding/)
  if (path.startsWith("s3://")) {
    const objectKey = path.replace("s3://", "");
    return `${API_BASE_URL}/api/v1/s3-files/${encodeURIComponent(objectKey)}?${params.toString()}`;
  }

  if (path.includes(":9000/vinfast-onboarding/")) {
    const objectKey = path.split(":9000/vinfast-onboarding/")[1];
    return `${API_BASE_URL}/api/v1/s3-files/${encodeURIComponent(objectKey)}?${params.toString()}`;
  }

  // Nếu path là link external public khác (ví dụ: youtube, s3 aws public)
  if (path.startsWith("http://") || path.startsWith("https://")) {
    // Nếu vẫn là localhost bất kỳ, convert sang s3-files
    if (path.includes("localhost:") || path.includes("127.0.0.1:")) {
      const parts = path.split("/");
      const lastPart = parts[parts.length - 1];
      return `${API_BASE_URL}/api/v1/s3-files/${encodeURIComponent(lastPart)}?${params.toString()}`;
    }
    return path;
  }

  const encodedPath = path.split("/").map(encodeURIComponent).join("/");
  return `${API_BASE_URL}/api/v1/files/${encodedPath}?${params.toString()}`;
};

// ---------------------------------------------------------------------------
// Chat API
// ---------------------------------------------------------------------------

export const chatApi = {
  ask: (message: string, conversation_id: string) =>
    api
      .post("/api/v1/chat", { message, conversation_id })
      .then((r) => r.data),

  getConversation: (conversation_id: string) =>
    api
      .get<ConversationHistoryResponse>(`/api/v1/chat/conversations/${encodeURIComponent(conversation_id)}`)
      .then((r) => r.data),

  /** Ghi nhận đánh giá ↑/−/↓ cho một câu trả lời AI */
  submitFeedback: (payload: FeedbackPayload) =>
    api
      .post<{ id: number; message: string }>("/api/v1/feedback", payload)
      .then((r) => r.data),
};

// ---------------------------------------------------------------------------
// Support Ticket API
// ---------------------------------------------------------------------------

export const supportApi = {
  /** Gửi form hỗ trợ (multipart/form-data để kèm file) */
  createTicket: (formData: FormData) =>
    api.post<SupportTicket>("/api/v1/auth/support/tickets", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then((r) => r.data),

  /** Manager: lấy danh sách tất cả tickets */
  listTickets: () =>
    api.get<SupportTicket[]>("/api/v1/auth/support/tickets").then((r) => r.data),

  /** Manager: đếm ticket chưa đọc */
  getUnreadCount: () =>
    api.get<UnreadCountResponse>("/api/v1/auth/support/tickets/unread-count").then((r) => r.data),

  /** Manager: đánh dấu đã đọc */
  markRead: (ticketId: string) =>
    api.patch<SupportTicket>(`/api/v1/auth/support/tickets/${ticketId}/read`).then((r) => r.data),

  /** Lấy presigned URL để xem/tải file đính kèm từ MinIO */
  getAttachmentUrl: (path: string) =>
    api.get<{ url: string }>(`/api/v1/auth/support/tickets/files/${path}`).then((r) => r.data.url),
};

// ---------------------------------------------------------------------------
// Manager API
// ---------------------------------------------------------------------------

export const managerApi = {
  getTeamProgress: () =>
    api.get<TeamProgressResponse>("/api/v1/auth/manager/team-progress").then((r) => r.data),
};

// ---------------------------------------------------------------------------
// Ingest API
// ---------------------------------------------------------------------------

export const ingestApi = {
  uploadDocument: (formData: FormData) =>
    api.post("/api/v1/ingest/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then((r) => r.data),
};

// ---------------------------------------------------------------------------
// Pending Update API
// ---------------------------------------------------------------------------

export const pendingUpdateApi = {
  getPendingUpdates: () =>
    api.get<PendingUpdate[]>("/api/v1/auth/pending-updates").then((r) => r.data),

  completePendingUpdate: (updateId: number) =>
    api.post(`/api/v1/auth/pending-updates/${updateId}/complete`).then((r) => r.data),
};

export default api;
