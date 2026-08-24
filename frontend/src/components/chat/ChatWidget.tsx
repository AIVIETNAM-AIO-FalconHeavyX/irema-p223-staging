import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "../../contexts/AuthContext";
import { chatApi } from "../../services/api";
import type { ChatMessage, RetrievedDocInfo } from "../../types";
import VideoSourcePlayer from "./VideoSourcePlayer";
import FeedbackWidget from "./FeedbackWidget";


interface ChatResponseData {
  response: string;
  analysis?: string;
  intent?: string;
  vehicle_model?: string;
  error_code?: string;
  citations?: string[];
  retrieved_docs?: RetrievedDocInfo[];
  needs_escalation?: boolean;
  ticket_payload?: Record<string, any>;
}


const ROLE_QUICK_PROMPTS: Record<string, string[]> = {
  accountant: [
    "Hướng dẫn đăng nhập hệ thống DMS",
    "Quy trình đặt hàng tồn kho PO",
    "Quy trình tạo yêu cầu mua sắm PR",
    "Chính sách bán hàng và hóa đơn XMĐ",
  ],
  accounting: [
    "Hướng dẫn đăng nhập hệ thống DMS",
    "Quy trình đặt hàng tồn kho PO",
    "Quy trình tạo yêu cầu mua sắm PR",
    "Chính sách bán hàng và hóa đơn XMĐ",
  ],
  sale: [
    "Quy trình bán hàng 8 bước chuẩn VinFast",
    "Chính sách ưu đãi lệ phí trước bạ xe máy điện",
    "Chính sách sạc miễn phí và thuê pin",
    "Hồ sơ giấy tờ khách hàng cần cung cấp",
  ],
  sales: [
    "Quy trình bán hàng 8 bước chuẩn VinFast",
    "Chính sách ưu đãi lệ phí trước bạ xe máy điện",
    "Chính sách sạc miễn phí và thuê pin",
    "Hồ sơ giấy tờ khách hàng cần cung cấp",
  ],
  technician: [
    "Quy trình sửa chữa pin xe máy điện cho XDV",
    "Nội dung chương trình chăm sóc xe miễn phí",
    "Kiểm tra 5 hạng mục bảo dưỡng định kỳ",
    "Chính sách bảo hành và sửa chữa xe",
  ],
  ktv: [
    "Quy trình sửa chữa pin xe máy điện cho XDV",
    "Nội dung chương trình chăm sóc xe miễn phí",
    "Kiểm tra 5 hạng mục bảo dưỡng định kỳ",
    "Chính sách bảo hành và sửa chữa xe",
  ],
  owner: [
    "Tổng quan quy trình hoạt động các phòng ban",
    "Chính sách bán hàng và thuê pin xe máy điện",
    "Quy trình đặt hàng PO và quản trị kho",
    "Tiêu chuẩn dịch vụ đại lý VinFast",
  ],
};

const INTENT_BADGES: Record<string, { label: string; color: string }> = {
  RAG_SEARCH: { label: "Tra cứu tài liệu", color: "#0f6b3a" },
  WORKFLOW: { label: "Sơ đồ quy trình", color: "#7c3aed" },
  TROUBLESHOOTING: { label: "Chẩn đoán sự cố", color: "#c98a1c" },
  CREATE_TICKET: { label: "Chuyển tiếp IT/Manager", color: "#e3543f" },
  GENERAL_QA: { label: "Hỏi đáp chung", color: "#1e6fb5" },
};

/**
 * Cohere relevance score is normalized to [0, 1].
 */
function getScoreColor(score: number): string {
  if (score >= 0.75) return "#0f6b3a";
  if (score >= 0.45) return "#1e6fb5";
  if (score >= 0.2) return "#c98a1c";
  return "#e3543f";
}

/**
 * Component hiển thị một source badge inline dưới chat response.
 */
function SourceBadge({ doc }: { doc: RetrievedDocInfo }) {
  const [showPreview, setShowPreview] = useState(false);
  const scoreColor = getScoreColor(doc.rerank_score);
  const scoreDisplay = `${Math.round(doc.rerank_score * 100)}%`;

  return (
    <div className="source-badge-wrapper">
      <button
        className="source-badge"
        onClick={() => setShowPreview((p) => !p)}
        title={`Xem preview nội dung chunk`}
        style={{ borderColor: `${scoreColor}40` }}
      >
        <span className="source-badge-icon">📄</span>
        <span className="source-badge-name">{doc.doc_name}</span>
        {doc.section && (
          <span className="source-badge-section">· {doc.section}</span>
        )}
        <span
          className="source-badge-score"
          style={{ background: `${scoreColor}18`, color: scoreColor }}
        >
          {scoreDisplay}
        </span>
      </button>
      {showPreview && doc.content_preview && (
        <div className="source-badge-preview">
          <p className="source-preview-text">{doc.content_preview}</p>
        </div>
      )}
    </div>
  );
}

function formatInlineText(text: string) {
  if (!text) return null;
  // Match bold **text**, code `code`, italic *text*
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g);

  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      const boldText = part.slice(2, -2);
      return (
        <strong key={i} style={{ fontWeight: 600 }}>
          {boldText}
        </strong>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      const codeText = part.slice(1, -1);
      return (
        <code
          key={i}
          style={{
            background: "rgba(0,0,0,0.06)",
            padding: "1px 4px",
            borderRadius: "4px",
            fontSize: "0.9em",
          }}
        >
          {codeText}
        </code>
      );
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      const italicText = part.slice(1, -1);
      return <em key={i}>{italicText}</em>;
    }
    // Clean any stray asterisks
    return part.replace(/\*\*/g, "");
  });
}

function renderFormattedContent(text: string) {
  if (!text) return null;

  const lines = text.split("\n");

  return (
    <div className="chat-formatted-body">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) {
          return <div key={idx} style={{ height: "6px" }} />;
        }

        // Heading ### or ## or #
        const headingMatch = trimmed.match(/^#{1,4}\s+(.*)$/);
        if (headingMatch) {
          return (
            <div
              key={idx}
              style={{
                fontWeight: 700,
                margin: "8px 0 4px",
                color: "inherit",
                fontSize: "1.05em",
              }}
            >
              {formatInlineText(headingMatch[1])}
            </div>
          );
        }

        // Bullet point - or *
        const bulletMatch = trimmed.match(/^[-*]\s+(.*)$/);
        if (bulletMatch) {
          return (
            <div
              key={idx}
              style={{
                display: "flex",
                gap: "6px",
                margin: "2px 0 2px 4px",
                alignItems: "flex-start",
              }}
            >
              <span style={{ color: "var(--green-700)", fontWeight: 700 }}>•</span>
              <div style={{ flex: 1 }}>{formatInlineText(bulletMatch[1])}</div>
            </div>
          );
        }

        // Numbered list 1. 2.
        const numMatch = trimmed.match(/^(\d+[\.)])\s+(.*)$/);
        if (numMatch) {
          return (
            <div
              key={idx}
              style={{
                display: "flex",
                gap: "6px",
                margin: "3px 0",
                alignItems: "flex-start",
              }}
            >
              <span style={{ fontWeight: 600, minWidth: "18px", color: "var(--green-700)" }}>
                {numMatch[1]}
              </span>
              <div style={{ flex: 1 }}>{formatInlineText(numMatch[2])}</div>
            </div>
          );
        }

        // Regular line
        return (
          <div key={idx} style={{ margin: "2px 0" }}>
            {formatInlineText(trimmed)}
          </div>
        );
      })}
    </div>
  );
}

export default function ChatWidget() {
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const conversationIdRef = useRef(crypto.randomUUID().replaceAll("-", ""));

  const roleKey = (user?.role || "sale").toLowerCase();
  const quickPrompts = ROLE_QUICK_PROMPTS[roleKey] || ROLE_QUICK_PROMPTS.sale;

  const [messages, setMessages] = useState<
    (ChatMessage & {
      intent?: string;
      citations?: string[];
      retrieved_docs?: RetrievedDocInfo[];
      needs_escalation?: boolean;
      ticket_payload?: Record<string, any>;
    })[]
  >([
    {
      role: "assistant",
      content: `Xin chào ${user?.full_name || "bạn"}! Tôi là **VF AI Assistant**. Tôi sẵn sàng hỗ trợ bạn tra cứu tài liệu chuyên môn và hướng dẫn nghiệp vụ chuẩn VinFast.`,
      timestamp: new Date(),
    },
  ]);

  // Update greeting when user changes
  useEffect(() => {
    if (user) {
      setMessages([
        {
          role: "assistant",
          content: `Xin chào ${user.full_name || "bạn"}! Tôi là **VF AI Assistant**. Tôi sẵn sàng hỗ trợ bạn tra cứu tài liệu chuyên môn và hướng dẫn nghiệp vụ chuẩn VinFast.`,
          timestamp: new Date(),
        },
      ]);
    }
  }, [user?.role, user?.full_name]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const handleSend = async (textToSend?: string) => {
    const query = (textToSend || input).trim();
    if (!query || loading) return;

    const userMsg = {
      role: "user" as const,
      content: query,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInput("");
    setLoading(true);

    try {
      const res: ChatResponseData = await chatApi.ask(query, conversationIdRef.current);

      const aiMsg = {
        role: "assistant" as const,
        content: res.response || "Tôi chưa tìm thấy câu trả lời phù hợp trong tài liệu.",
        citations: res.citations || [],
        retrieved_docs: res.retrieved_docs || [],
        intent: res.intent,
        needs_escalation: res.needs_escalation,
        ticket_payload: res.ticket_payload,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "⚠ Không thể kết nối với server AI. Vui lòng kiểm tra lại backend (port 8001).",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-widget-root">
      {/* Floating Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="chat-window"
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
          >
            {/* Window Header */}
            <div className="chat-header">
              <div className="chat-header-brand">
                <div className="chat-avatar-sm">🤖</div>
                <div>
                  <h3 className="chat-title">VF AI Assistant</h3>
                  <div className="chat-status">
                    <span className="status-dot" /> Online · AI Trợ lý Đại lý
                  </div>
                </div>
              </div>

              <div className="chat-header-actions">
                <button
                  className="chat-close-btn"
                  onClick={() => setIsOpen(false)}
                  title="Đóng Chatbot"
                >
                  ✕
                </button>
              </div>
            </div>


            {/* Messages Container */}
            <div className="chat-body">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`chat-bubble-row ${msg.role === "user" ? "user-row" : "ai-row"
                    }`}
                >
                  {msg.role === "assistant" && (
                    <div className="chat-avatar">🤖</div>
                  )}

                  <div className={`chat-bubble ${msg.role}`}>
                    {/* Intent Badge */}
                    {msg.intent && INTENT_BADGES[msg.intent] && (
                      <span
                        className="intent-badge"
                        style={{
                          background: `${INTENT_BADGES[msg.intent].color}15`,
                          color: INTENT_BADGES[msg.intent].color,
                        }}
                      >
                        ● {INTENT_BADGES[msg.intent].label}
                      </span>
                    )}

                    {/* Message content */}
                    <div className="chat-text">{renderFormattedContent(msg.content)}</div>

                    {/* Video Player (nếu có chunk từ video) */}
                    {(() => {
                      if (!msg.retrieved_docs || msg.retrieved_docs.length === 0) return null;
                      // Nhóm chunks video theo source_path
                      const videoChunks = msg.retrieved_docs.filter(
                        (d) => d.content_type === "video" && d.source_path
                      );
                      if (videoChunks.length === 0) return null;
                      // Lấy video có nhiều chunk nhất (1 video trên mỗi response)
                      const byPath: Record<string, RetrievedDocInfo[]> = {};
                      videoChunks.forEach((c) => {
                        if (!byPath[c.source_path]) byPath[c.source_path] = [];
                        byPath[c.source_path].push(c);
                      });
                      const primaryPath = Object.keys(byPath).reduce((a, b) =>
                        byPath[a].length >= byPath[b].length ? a : b
                      );
                      const primaryChunks = byPath[primaryPath];
                      // Primary chunk = chunk có rerank_score cao nhất
                      const primaryChunk = primaryChunks.reduce((a, b) =>
                        a.rerank_score >= b.rerank_score ? a : b
                      );
                      return (
                        <VideoSourcePlayer
                          key={primaryPath}
                          primaryChunk={primaryChunk}
                          allChunks={primaryChunks}
                          className="chat-video-player"
                        />
                      );
                    })()}

                    {/* Inline Source Badges (Retrieved Docs với rerank score) */}
                    {msg.retrieved_docs && msg.retrieved_docs.length > 0 && (
                      <div className="chat-source-docs">
                        <span className="source-docs-label">🔍 Nguồn tra cứu:</span>
                        <div className="source-badges-list">
                          {msg.retrieved_docs.map((doc, di) => (
                            <SourceBadge key={di} doc={doc} />
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Citations */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="chat-citations">
                        <span className="citation-title">📚 Trích dẫn nguồn:</span>
                        {msg.citations.map((c, ci) => (
                          <span key={ci} className="citation-pill">
                            {c}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Ticket Payload if escalated */}
                    {msg.needs_escalation && msg.ticket_payload && (
                      <div className="chat-ticket-box">
                        <div className="ticket-header">
                          <span>🎫 Yêu Cầu Hỗ Trợ Đã Tạo</span>
                          <span className="ticket-priority">
                            {msg.ticket_payload.priority || "NORMAL"}
                          </span>
                        </div>
                        <div className="ticket-body">
                          <p>
                            <strong>Tiêu đề:</strong> {msg.ticket_payload.title}
                          </p>
                          <p>
                            <strong>Bộ phận:</strong> {msg.ticket_payload.department}
                          </p>
                          <p>
                            <strong>Chi tiết:</strong>{" "}
                            {msg.ticket_payload.description}
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Timestamp */}
                    <span className="chat-time">
                      {new Date(msg.timestamp).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>

                    {/* Feedback Widget — chỉ hiển thị cho AI messages (trừ greeting) */}
                    {msg.role === "assistant" && i > 0 && (
                      <FeedbackWidget
                        query={
                          // Lấy tin nhắn user liền trước AI message này
                          messages[i - 1]?.role === "user"
                            ? messages[i - 1].content
                            : ""
                        }
                        response={msg.content}
                        intent={msg.intent}
                        retrievedDocs={msg.retrieved_docs}
                      />
                    )}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="chat-bubble-row ai-row">
                  <div className="chat-avatar">🤖</div>
                  <div className="chat-bubble assistant loading-bubble">
                    <span className="dot-flashing" />
                    <span className="dot-flashing" />
                    <span className="dot-flashing" />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Quick Prompts */}
            {messages.length < 3 && (
              <div className="quick-prompts">
                {quickPrompts.map((prompt, pi) => (
                  <button
                    key={pi}
                    className="prompt-chip"
                    onClick={() => handleSend(prompt)}
                  >
                    💡 {prompt}
                  </button>
                ))}
              </div>
            )}

            {/* Input Bar */}
            <form
              className="chat-footer"
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
            >
              <input
                type="text"
                className="chat-input"
                placeholder="Hỏi AI về quy trình, mã lỗi, tài liệu..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={loading}
              />
              <button
                type="submit"
                className="chat-send-btn"
                disabled={!input.trim() || loading}
                title="Gửi câu hỏi"
              >
                ➤
              </button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Floating Toggle Button */}
      <motion.button
        className={`chat-toggle-btn ${isOpen ? "active" : ""}`}
        onClick={() => setIsOpen((o) => !o)}
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.95 }}
        title={isOpen ? "Thu nhỏ Chatbot" : "Hỏi AI Trợ Lý Đại Lý"}
      >
        <span className="chat-btn-icon">{isOpen ? "✕" : "💬"}</span>
        {!isOpen && <span className="chat-btn-pulse" />}
        {!isOpen && <span className="chat-btn-label">Hỏi AI</span>}
      </motion.button>
    </div>
  );
}
