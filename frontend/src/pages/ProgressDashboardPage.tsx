import { useEffect, useState } from "react";
import { managerApi } from "../services/api";
import type { TeamMemberProgress, TeamProgressResponse, UserRole } from "../types";
import { ROLE_LABELS } from "../types";

const STATUS_LABEL: Record<string, string> = {
  not_started: "Chưa bắt đầu",
  in_progress: "Đang học",
  completed: "Hoàn thành",
};

const STATUS_CLASS: Record<string, string> = {
  not_started: "pd-status-none",
  in_progress: "pd-status-active",
  completed: "pd-status-done",
};

const ROLE_BG: Record<string, string> = {
  accountant: "#1e6fb5",
  technician: "#c98a1c",
  sale: "#7c3aed",
  manager: "#0f6b3a",
  owner: "#0f6b3a",
};

function MemberRow({ member }: { member: TeamMemberProgress }) {
  const initials = member.full_name
    .split(" ")
    .slice(-2)
    .map((w) => w[0])
    .join("")
    .toUpperCase() || "??";

  const pct = member.onboarding_progress;

  return (
    <div className="pd-member-row">
      <div className="pd-member-avatar" style={{ background: ROLE_BG[member.role] || "#555" }}>
        {initials}
      </div>
      <div className="pd-member-info">
        <span className="pd-member-name">{member.full_name}</span>
        <div className="pd-member-meta">
          <span className={`pd-role-badge pd-role-${member.role}`}>
            {ROLE_LABELS[member.role as UserRole] || member.role}
          </span>
          <span className="pd-member-email">• {member.email}</span>
        </div>
      </div>
      <div className="pd-member-progress">
        <div className="pd-progress-bar-wrap">
          <div
            className="pd-progress-bar-fill"
            style={{ width: `${pct}%`, background: pct >= 100 ? "var(--green-600)" : "#3b82f6" }}
          />
        </div>
        <span className="pd-progress-pct">{pct}%</span>
      </div>
      <div className="pd-member-steps">
        <span className="pd-steps-text">
          {member.completed_steps}/{member.total_steps || "—"} bài
        </span>
      </div>
      <div className="pd-member-status">
        <span className={`pd-status-badge ${STATUS_CLASS[member.status]}`}>
          {STATUS_LABEL[member.status]}
        </span>
      </div>
    </div>
  );
}

export default function ProgressDashboardPage() {
  const [data, setData] = useState<TeamProgressResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filterRole, setFilterRole] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");

  useEffect(() => {
    managerApi.getTeamProgress()
      .then(setData)
      .catch(() => setError("Không thể tải dữ liệu. Vui lòng thử lại."))
      .finally(() => setLoading(false));
  }, []);

  const filteredUsers = (data?.users || []).filter((u) => {
    const roleMatch = filterRole === "all" || u.role === filterRole;
    const statusMatch = filterStatus === "all" || u.status === filterStatus;
    return roleMatch && statusMatch;
  });

  return (
    <div className="pd-page" id="progress-dashboard-page">
      {/* Header */}
      <div className="pd-header">
        <div>
          <h1 className="pd-title">Quản lý</h1>
          <p className="pd-subtitle">Xem tiến độ onboarding của nhân viên</p>
        </div>
      </div>

      {loading ? (
        <div className="pd-loading">
          <div className="pd-spinner" />
          <p>Đang tải dữ liệu...</p>
        </div>
      ) : error ? (
        <div className="pd-error">{error}</div>
      ) : data && (
        <>
          {/* Stats cards */}
          <div className="pd-stats-row">
            <div className="pd-stat-card">
              <span className="pd-stat-number">{data.total}</span>
              <span className="pd-stat-label">Nhân viên</span>
            </div>
            <div className="pd-stat-card">
              <span className="pd-stat-number">{data.in_progress}</span>
              <span className="pd-stat-label">Đang học</span>
            </div>
            <div className="pd-stat-card">
              <span className="pd-stat-number">{data.completed}</span>
              <span className="pd-stat-label">Đã hoàn thành</span>
            </div>
          </div>

          {/* Filters */}
          <div className="pd-filters">
            <div className="pd-filter-group">
              <label className="pd-filter-label">Vai trò</label>
              <select
                className="pd-filter-select"
                value={filterRole}
                onChange={(e) => setFilterRole(e.target.value)}
              >
                <option value="all">Tất cả</option>
                <option value="sale">Nhân viên kinh doanh</option>
                <option value="accountant">Kế toán</option>
                <option value="technician">Kỹ thuật viên</option>
                <option value="manager">Quản lý</option>
              </select>
            </div>
            <div className="pd-filter-group">
              <label className="pd-filter-label">Trạng thái</label>
              <select
                className="pd-filter-select"
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
              >
                <option value="all">Tất cả</option>
                <option value="not_started">Chưa bắt đầu</option>
                <option value="in_progress">Đang học</option>
                <option value="completed">Đã hoàn thành</option>
              </select>
            </div>
          </div>

          {/* Member list */}
          <div className="pd-list-card">
            <h2 className="pd-list-title">Danh sách nhân viên</h2>
            {filteredUsers.length === 0 ? (
              <div className="pd-empty">Không có nhân viên phù hợp với bộ lọc.</div>
            ) : (
              <div className="pd-member-list">
                {filteredUsers.map((member) => (
                  <MemberRow key={member.id} member={member} />
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
