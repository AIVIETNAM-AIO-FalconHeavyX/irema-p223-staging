import { useEffect, useState } from "react";
import { supportApi } from "../services/api";
import type { SupportTicket } from "../types";
import { ROLE_LABELS } from "../types";

const STATUS_LABELS: Record<string, string> = {
  open: "Mới",
  read: "Đã đọc",
  resolved: "Đã giải quyết",
};

function formatRelativeTime(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "Vừa xong";
  if (minutes < 60) return `${minutes} phút trước`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} giờ trước`;
  const days = Math.floor(hours / 24);
  return `${days} ngày trước`;
}

function RoleAvatar({ role, name }: { role: string; name: string }) {
  const initials = name
    .split(" ")
    .slice(-2)
    .map((w) => w[0])
    .join("")
    .toUpperCase() || "??";

  const colors: Record<string, string> = {
    accountant: "#1e6fb5",
    technician: "#c98a1c",
    sale: "#7c3aed",
    manager: "#0f6b3a",
    owner: "#0f6b3a",
  };
  const bg = colors[role] || "#666";

  return (
    <div className="si-avatar" style={{ background: bg }}>
      {initials}
    </div>
  );
}

export default function SupportInboxPage() {
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    supportApi.listTickets()
      .then((data) => setTickets(data))
      .catch(() => setTickets([]))
      .finally(() => setLoading(false));
  }, []);

  const handleExpand = async (ticket: SupportTicket) => {
    setExpandedId(prev => prev === ticket.id ? null : ticket.id);
    if (ticket.status === "open") {
      try {
        const updated = await supportApi.markRead(ticket.id);
        setTickets(prev => prev.map(t => t.id === ticket.id ? updated : t));
      } catch {
        // ignore
      }
    }
  };

  const handleViewAttachment = async (e: React.MouseEvent, path: string) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      const url = await supportApi.getAttachmentUrl(path);
      window.open(url, "_blank");
    } catch {
      alert("Không thể tải file đính kèm. Vui lòng thử lại sau.");
    }
  };

  const openCount = tickets.filter(t => t.status === "open").length;

  return (
    <div className="si-page" id="support-inbox-page">
      {/* Header */}
      <div className="si-header">
        <div>
          <h1 className="si-title">
            Hộp thư Hỗ trợ
            {openCount > 0 && <span className="si-badge-header">{openCount} mới</span>}
          </h1>
          <p className="si-subtitle">Yêu cầu hỗ trợ từ nhân viên đại lý</p>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="si-loading">
          <div className="si-spinner" />
          <p>Đang tải yêu cầu hỗ trợ...</p>
        </div>
      ) : tickets.length === 0 ? (
        <div className="si-empty">
          <div className="si-empty-icon">📭</div>
          <h3>Chưa có yêu cầu hỗ trợ nào</h3>
          <p>Khi nhân viên gửi yêu cầu, chúng sẽ xuất hiện ở đây.</p>
        </div>
      ) : (
        <div className="si-list">
          {tickets.map((ticket) => {
            const isExpanded = expandedId === ticket.id;
            const isUnread = ticket.status === "open";
            return (
              <div
                key={ticket.id}
                className={`si-ticket ${isUnread ? "si-ticket-unread" : ""} ${isExpanded ? "si-ticket-expanded" : ""}`}
                onClick={() => handleExpand(ticket)}
              >
                <div className="si-ticket-header">
                  <RoleAvatar role={ticket.sender_role} name={ticket.sender_name} />
                  <div className="si-ticket-meta">
                    <div className="si-ticket-name-row">
                      <span className="si-sender-name">{ticket.sender_name}</span>
                      {isUnread && <span className="si-unread-dot" />}
                      <span className={`si-role-badge si-role-${ticket.sender_role}`}>
                        {ROLE_LABELS[ticket.sender_role as keyof typeof ROLE_LABELS] || ticket.sender_role}
                      </span>
                    </div>
                    <div className="si-ticket-info-row">
                      <span className="si-agency-code">🏢 {ticket.agency_id}</span>
                      <span className="si-time">{formatRelativeTime(ticket.created_at)}</span>
                    </div>
                    <p className={`si-description-preview ${isExpanded ? "si-expanded" : ""}`}>
                      {ticket.description}
                    </p>
                  </div>
                  <div className="si-ticket-right">
                    <span className={`si-status-badge si-status-${ticket.status}`}>
                      {STATUS_LABELS[ticket.status]}
                    </span>
                    <span className="si-expand-arrow">{isExpanded ? "▲" : "▼"}</span>
                  </div>
                </div>

                {isExpanded && ticket.attachment_path && (
                  <div className="si-ticket-attachment">
                    <span className="si-attachment-label">📎 File đính kèm:</span>
                    <a
                      href="#"
                      className="si-attachment-link"
                      onClick={(e) => handleViewAttachment(e, ticket.attachment_path!)}
                    >
                      Xem / Tải file
                    </a>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
