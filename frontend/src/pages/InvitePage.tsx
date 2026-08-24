import { useState } from "react";
import { motion } from "framer-motion";
import { useAuth } from "../contexts/AuthContext";
import type { UserRole } from "../types";
import { ROLE_LABELS } from "../types";

const INVITABLE_ROLES: UserRole[] = ["accountant", "technician", "sale", "manager"];

interface InviteRecord {
  email: string;
  role: string;
  sentAt: string;
}

export default function InvitePage() {
  const { invite } = useAuth();
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<UserRole>("sale");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [sent, setSent] = useState<InviteRecord[]>([]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await invite({ email, role });
      setSent((prev) => [
        { email, role, sentAt: new Date().toLocaleString("vi-VN") },
        ...prev,
      ]);
      setEmail("");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Gửi lời mời thất bại.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="invite-page" id="invite-page">
      <motion.div
        className="page-header"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1>Mời Thành Viên</h1>
        <p className="subtitle">Thêm nhân viên vào đại lý và phân quyền theo vai trò.</p>
      </motion.div>

      <div className="invite-layout">
        {/* Invite form */}
        <motion.div
          className="card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <h2 className="card-title">Gửi lời mời</h2>
          <form onSubmit={handleSubmit} className="auth-form" id="invite-form">
            <div className="form-group">
              <label htmlFor="invite-email">Email nhân viên</label>
              <input
                id="invite-email"
                type="email"
                placeholder="nhanvien@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="invite-role">Vai trò</label>
              <select
                id="invite-role"
                value={role}
                onChange={(e) => setRole(e.target.value as UserRole)}
              >
                {INVITABLE_ROLES.map((r) => (
                  <option key={r} value={r}>
                    {ROLE_LABELS[r]}
                  </option>
                ))}
              </select>
            </div>

            {error && (
              <div className="alert alert-error">⚠ {error}</div>
            )}

            <button
              type="submit"
              className="btn-primary"
              id="invite-submit-btn"
              disabled={loading}
            >
              {loading ? "Đang gửi..." : "📨 Gửi lời mời"}
            </button>
          </form>
        </motion.div>

        {/* Invite history */}
        <motion.div
          className="card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <h2 className="card-title">Lời mời đã gửi</h2>
          {sent.length === 0 ? (
            <div className="empty-state">
              <p>📭 Chưa có lời mời nào được gửi trong phiên này.</p>
            </div>
          ) : (
            <div className="invite-list">
              {sent.map((inv, i) => (
                <motion.div
                  key={i}
                  className="invite-item"
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  id={`invite-item-${i}`}
                >
                  <div className="invite-info">
                    <strong>{inv.email}</strong>
                    <span className="role-badge">{ROLE_LABELS[inv.role as UserRole]}</span>
                    <span className="invite-time">{inv.sentAt}</span>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
