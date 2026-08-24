import { useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { authApi } from "../services/api";
import { useAuth } from "../contexts/AuthContext";

export default function InviteAcceptPage() {
  const [params] = useSearchParams();
  const token = params.get("token") || "";
  const navigate = useNavigate();
  const { login } = useAuth();
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await authApi.acceptInvite({ token, full_name: fullName, password });
      await login({ email: result.user.email, password });
      navigate("/", { replace: true });
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || "This invitation is invalid or has expired.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-right">
        <div className="auth-card">
          <div className="auth-card-header">
            <h2>Accept invitation</h2>
            <p>Create your password to join the dealership.</p>
          </div>
          <form onSubmit={submit} className="auth-form">
            <div className="form-group">
              <label htmlFor="invite-full-name">Full name</label>
              <input id="invite-full-name" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
            </div>
            <div className="form-group">
              <label htmlFor="invite-password">Password</label>
              <input id="invite-password" type="password" minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>
            {error && <div className="alert alert-error">{error}</div>}
            <button type="submit" className="btn-primary btn-full" disabled={loading || !token}>
              {loading ? "Creating account..." : "Create account"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
