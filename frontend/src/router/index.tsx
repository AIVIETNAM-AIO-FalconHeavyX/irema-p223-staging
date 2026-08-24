import { createBrowserRouter, Navigate, RouterProvider } from "react-router-dom";
import { AuthProvider, useAuth } from "../contexts/AuthContext";
import ProtectedRoute from "../components/auth/ProtectedRoute";
import AppShell from "../components/layout/AppShell";
import LoginPage from "../pages/LoginPage";
import RegisterPage from "../pages/RegisterPage";
import InviteAcceptPage from "../pages/InviteAcceptPage";
import OnboardingPage from "../pages/OnboardingPage";
import InvitePage from "../pages/InvitePage";
import SupportInboxPage from "../pages/SupportInboxPage";
import ProgressDashboardPage from "../pages/ProgressDashboardPage";
import CourseViewerPage from "../pages/CourseViewerPage";
import FileExplorerPage from "../pages/FileExplorerPage";

const RootRedirect = () => {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === "vinfast") return <Navigate to="/files" replace />;
  if (user.role === "owner") return <Navigate to="/progress" replace />;
  return <Navigate to="/onboarding" replace />;
};

const router = createBrowserRouter([
  // Public routes
  { path: "/login", element: <LoginPage /> },
  { path: "/register", element: <RegisterPage /> },
  { path: "/invite/accept", element: <InviteAcceptPage /> },
  {
    path: "/resource",
    element: (
      <ProtectedRoute>
        <CourseViewerPage />
      </ProtectedRoute>
    ),
  },

  // Protected routes — wrapped in AppShell
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <AppShell />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <RootRedirect /> },
      { path: "onboarding", element: <OnboardingPage /> },
      { path: "library", element: <Navigate to="/onboarding" replace /> },
      { path: "files", element: <ProtectedRoute requiredRole={["vinfast", "owner"]}><FileExplorerPage /></ProtectedRoute> },
      {
        path: "invite",
        element: (
          <ProtectedRoute requiredRole="owner">
            <InvitePage />
          </ProtectedRoute>
        ),
      },
      {
        path: "support",
        element: (
          <ProtectedRoute requiredRole="vinfast">
            <SupportInboxPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "progress",
        element: (
          <ProtectedRoute requiredRole={["manager", "owner"]}>
            <ProgressDashboardPage />
          </ProtectedRoute>
        ),
      },
    ],
  },

  // Fallback
  { path: "*", element: <Navigate to="/" replace /> },
]);

export default function AppRouter() {
  return (
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  );
}
