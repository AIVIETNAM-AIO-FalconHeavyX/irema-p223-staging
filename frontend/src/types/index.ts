// TypeScript types for VF AI Onboarding System

export type UserRole = "owner" | "accountant" | "technician" | "sale" | "manager" | "vinfast";

// ... Skipping intermediate lines, I need to do this carefully. I should view the file first or use multiple replacements.
export type UserStatus = "active" | "pending" | "inactive";
export type StepType = "document" | "video" | "quiz" | "task";

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  agency_id: string | null;
  status: UserStatus;
  onboarding_progress: number;
  created_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
  role: UserRole;
  agency_id?: string;
}

export interface InvitePayload {
  email: string;
  role: UserRole;
}

export interface InviteResponse {
  id: string;
  email: string;
  role: UserRole;
  token?: string | null;
  accepted: boolean;
  created_at: string;
}

export interface GuideItem {
  letter: string;
  title: string;
  desc: string;
}

export interface OnboardingResource {
  name: string;
  /** "video" hiển thị bằng thẻ <video>, "doc" mở PDF hoặc tải xuống */
  type: "video" | "doc";
  /** Đường dẫn tương đối trong data/raw hoặc URL MinIO, dùng để gọi /api/v1/files */
  path: string;
  /** Loại file & dung lượng thật, ví dụ "PDF · 2.1 MB" */
  meta: string;
  section_id?: string;
}

export interface QuizQuestion {
  id: number;
  question: string;
  options: string[];
  correctIndex: number;
  explanation: string;
}

export interface OnboardingStep {
  id: number;
  role_target: string;
  order: number;
  title: string;
  /** Nhãn ngắn dùng cho sidebar; `title` đầy đủ dùng cho tiêu đề trang */
  short_title: string;
  description: string;
  step_type: StepType;
  resource_url: string | null;
  duration_minutes: number;
  is_required: boolean;
  goal: string;
  guides: GuideItem[];
  resources: OnboardingResource[];
  quiz: QuizQuestion[];
}

export interface OnboardingProgress {
  progress: number;
  completed_step_ids: number[];
  completed_section_ids: string[];
  total_steps: number;
  modules: ModuleStatus[];
}

export interface ModuleStatus {
  module_id: number;
  unlocked: boolean;
  completed: boolean;
  quiz_score: number | null;
  step_ids: number[];
}

/**
 * Metadata của một chunk đã rerank — dùng để hiển thị inline source badges trong ChatWidget.
 * Tương ứng với Pydantic model `RetrievedDocInfo` trên backend.
 */
export interface RetrievedDocInfo {
  doc_name: string;
  section: string;
  rerank_score: number;   // Cross-Encoder logit score, có thể âm
  rrf_score: number;      // Reciprocal Rank Fusion score
  content_preview: string; // 150 ký tự đầu của chunk
  // Video support fields
  content_type: string;        // 'video' | 'document'
  source_path: string;         // Đường dẫn file gốc (để build video URL)
  timestamp_seconds: number | null; // Giây trong video để auto-seek
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  intent?: string;          // Intent được phân loại từ backend
  citations?: string[];
  retrieved_docs?: RetrievedDocInfo[]; // Source badges với rerank score — dùng để debug RAG
  timestamp: Date;
}

export interface ConversationHistoryMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  metadata?: {
    analysis?: string;
    intent?: string;
    citations?: string[];
    retrieved_docs?: RetrievedDocInfo[];
    needs_escalation?: boolean;
    ticket_payload?: Record<string, any> | null;
  };
  timestamp: string;
}

export interface ConversationHistoryResponse {
  conversation_id: string;
  messages: ConversationHistoryMessage[];
}

/**
 * Payload gửi feedback ↑/−/↓ lên backend POST /api/v1/feedback.
 * Khớp với FeedbackRequest Pydantic model.
 */
export interface FeedbackPayload {
  query: string;
  response: string;
  intent?: string;
  citations: string[];
  rerank_scores: number[];
  rag_confidence?: number;
  rating: "up" | "neutral" | "down";
}

export const ROLE_LABELS: Record<UserRole, string> = {
  owner: "Chủ đại lý",
  accountant: "Kế toán",
  technician: "Kỹ thuật viên",
  sale: "Nhân viên kinh doanh",
  manager: "Quản lý",
  vinfast: "VinFast Admin",
};

export const ROLE_COLORS: Record<UserRole, string> = {
  owner: "#0f6b3a",
  accountant: "#1e6fb5",
  technician: "#c98a1c",
  sale: "#7c3aed",
  manager: "#0f6b3a",
  vinfast: "#e3000f",
};

// ---------------------------------------------------------------------------
// Support Ticket Types
// ---------------------------------------------------------------------------

export interface SupportTicket {
  id: string;
  sender_id: string;
  sender_role: string;
  sender_name: string;
  agency_id: string;
  description: string;
  attachment_path: string | null;
  attachment_mime: string | null;
  status: "open" | "read" | "resolved";
  created_at: string;
}

export interface UnreadCountResponse {
  unread_count: number;
}

// ---------------------------------------------------------------------------
// Manager Team Progress Types
// ---------------------------------------------------------------------------

export interface TeamMemberProgress {
  id: string;
  full_name: string;
  email: string;
  role: UserRole;
  agency_id: string;
  onboarding_progress: number;
  completed_steps: number;
  total_steps: number;
  status: "not_started" | "in_progress" | "completed";
}

export interface TeamProgressResponse {
  total: number;
  in_progress: number;
  completed: number;
  not_started: number;
  users: TeamMemberProgress[];
}


// ---------------------------------------------------------------------------
// Pending Update Types
// ---------------------------------------------------------------------------

export interface PendingUpdate {
  id: number;
  step_id: number;
  is_completed: boolean;
  created_at: string;
  step: OnboardingStep;
}

