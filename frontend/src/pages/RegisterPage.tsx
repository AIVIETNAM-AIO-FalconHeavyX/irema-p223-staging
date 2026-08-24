import { Link } from "react-router-dom";

export default function RegisterPage() {
  return (
    <div className="auth-page">
      <div className="auth-left">
        <div className="auth-brand">
          <div className="auth-logo">VF</div>
          <h1>Tạo tài khoản</h1>
          <p>Tài khoản chỉ được tạo bằng lời mời từ quản trị viên.</p>
        </div>
      </div>

      <div className="auth-right">
        <div className="auth-card">
          <div className="auth-card-header">
            <h2>Cần lời mời</h2>
            <p>Vui lòng dùng liên kết trong email mời để thiết lập mật khẩu và kích hoạt tài khoản.</p>
          </div>
          <p className="auth-switch">
            Đã có lời mời? Mở liên kết trong email.{" "}
            <Link to="/login" id="goto-login-link">
              Đăng nhập
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
