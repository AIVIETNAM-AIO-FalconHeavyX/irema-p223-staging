import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuth } from "../contexts/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login({ email, password });
      const destination = (location.state as { from?: { pathname?: string; search?: string } } | null)?.from;
      navigate(destination ? `${destination.pathname || "/"}${destination.search || ""}` : "/", { replace: true });
    } catch (err: unknown) {
      setError("Tài khoản hoặc mật khẩu đã sai, xin vui lòng nhập lại!");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      {/* Left panel — decorative */}
      <div className="auth-left">
        <motion.div
          className="auth-brand"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h1>VF AI Onboarding</h1>
          <p>Hệ thống hỗ trợ đào tạo & vận hành<br />Đại lý Phân phối Xe Máy Điện</p>
        </motion.div>

        {/* Feature highlights */}
        <motion.div
          className="auth-features"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
        >
          {[
            { icon: "🤖", text: "AI trả lời câu hỏi nghiệp vụ 24/7" },
            { icon: "📚", text: "Tài liệu onboarding theo vai trò" },
            { icon: "🔒", text: "Phân quyền bảo mật RBAC" },
            { icon: "📊", text: "Theo dõi tiến độ đào tạo" },
          ].map((f, i) => (
            <motion.div
              key={i}
              className="feature-chip"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5 + i * 0.1 }}
            >
              <span>{f.icon}</span>
              <span>{f.text}</span>
            </motion.div>
          ))}
        </motion.div>
      </div>

      {/* Right panel — form */}
      <div className="auth-right">
        <motion.div
          className="auth-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <div className="auth-card-header">
            <h2>Đăng nhập</h2>
            <p>Chào mừng trở lại! Nhập thông tin để tiếp tục.</p>
          </div>

          <form onSubmit={handleSubmit} className="auth-form" id="login-form">
            <div className="form-group">
              <label htmlFor="login-email">Email</label>
              <input
                id="login-email"
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>

            <div className="form-group">
              <label htmlFor="login-password">Mật khẩu</label>
              <input
                id="login-password"
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>

            {error && (
              <motion.div
                className="alert alert-error"
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
              >
                ⚠ {error}
              </motion.div>
            )}

            <button
              type="submit"
              className="btn-primary btn-full"
              id="login-submit-btn"
              disabled={loading}
            >
              {loading ? (
                <span className="btn-loading">
                  <span className="spinner-sm" /> Đang đăng nhập...
                </span>
              ) : (
                "Đăng nhập →"
              )}
            </button>
          </form>

          <p className="auth-switch">
            Chưa có tài khoản?{" "}
            <Link to="/register" id="goto-register-link">
              Đăng ký
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
