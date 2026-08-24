import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuth } from "../contexts/AuthContext";
export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    email: "",
    password: "",
    full_name: "",
    role: "sale" as const,
    agency_id: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const update = (field: string, val: string) =>
    setForm((f) => ({ ...f, [field]: val }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (form.password.length < 8) {
      setError("Mật khẩu tối thiểu 8 ký tự.");
      return;
    }
    setLoading(true);
    try {
      await register({
        ...form,
        agency_id: form.agency_id || undefined,
      });
      navigate("/onboarding");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Đăng ký thất bại.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-left">
        <motion.div
          className="auth-brand"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="auth-logo">VF</div>
              <h1>Tạo tài khoản</h1>
              <p>Tạo tài khoản sale để bắt đầu<br />quy trình onboarding đại lý VF.</p>
        </motion.div>

        <motion.div
          className="auth-steps-hint"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          <div className="step-hint">
            <span className="step-num">1</span>
                <span>Đăng ký tài khoản sale</span>
          </div>
          <div className="step-hint">
            <span className="step-num">2</span>
            <span>Hoàn thành onboarding</span>
          </div>
          <div className="step-hint">
            <span className="step-num">3</span>
            <span>Mời nhân viên tham gia</span>
          </div>
        </motion.div>
      </div>

      <div className="auth-right">
        <motion.div
          className="auth-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="auth-card-header">
            <h2>Đăng ký</h2>
            <p>Điền đầy đủ thông tin để tạo tài khoản sale.</p>
          </div>

          <form onSubmit={handleSubmit} className="auth-form" id="register-form">
            <div className="form-group">
              <label htmlFor="reg-name">Họ và tên</label>
              <input
                id="reg-name"
                type="text"
                placeholder="Nguyễn Văn A"
                value={form.full_name}
                onChange={(e) => update("full_name", e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="reg-email">Email</label>
              <input
                id="reg-email"
                type="email"
                placeholder="owner@vf-daily.vn"
                value={form.email}
                onChange={(e) => update("email", e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="reg-password">Mật khẩu</label>
              <input
                id="reg-password"
                type="password"
                placeholder="Tối thiểu 8 ký tự"
                value={form.password}
                onChange={(e) => update("password", e.target.value)}
                required
                minLength={8}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="reg-agency">Mã đại lý (tuỳ chọn)</label>
                <input
                  id="reg-agency"
                  type="text"
                  placeholder="VF-HN-001"
                  value={form.agency_id}
                  onChange={(e) => update("agency_id", e.target.value)}
                />
              </div>
            </div>

            {error && (
              <motion.div
                className="alert alert-error"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                ⚠ {error}
              </motion.div>
            )}

            <button
              type="submit"
              className="btn-primary btn-full"
              id="register-submit-btn"
              disabled={loading}
            >
              {loading ? (
                <span className="btn-loading">
                  <span className="spinner-sm" /> Đang tạo tài khoản...
                </span>
              ) : (
                "Tạo tài khoản →"
              )}
            </button>
          </form>

          <p className="auth-switch">
            Đã có tài khoản?{" "}
            <Link to="/login" id="goto-login-link">
              Đăng nhập
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
