import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import type { UserRole } from "../../types";

interface ProtectedRouteProps {
  children: React.ReactNode;
  /** Nếu truyền vào, chỉ những role này mới được vào.
   *  "manager" → cho phép cả manager và owner.  */
  requiredRole?: UserRole | UserRole[];
}

export default function ProtectedRoute({ children, requiredRole }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner" />
        <p>Đang tải...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredRole && user) {
    const allowed = Array.isArray(requiredRole) ? requiredRole : [requiredRole];
    // "manager" routes cũng mở cho owner
    const effectiveAllowed = allowed.includes("manager" as UserRole)
      ? [...allowed, "owner" as UserRole]
      : allowed;
    if (!effectiveAllowed.includes(user.role)) {
      return <Navigate to="/" replace />;
    }
  }

  return <>{children}</>;
}
