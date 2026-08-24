import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { ChartNoAxesColumnIncreasing, CircleHelp, ClipboardList, LogOut, Menu, UserPlus, X, Upload } from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import { ROLE_LABELS } from "../../types";
import ChatWidget from "../chat/ChatWidget";
import SupportModal from "../support/SupportModal";
import { supportApi } from "../../services/api";

import PendingQuizModal from "../onboarding/PendingQuizModal";

export default function AppShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [showSupportModal, setShowSupportModal] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const isVinfast = user?.role === "vinfast";
  const isManagerOrOwner = user?.role === "manager" || user?.role === "owner";
  const isOwner = user?.role === "owner";

  // Pending updates for forced quizzes
  const [, setPendingUpdates] = useState<import("../../types").PendingUpdate[]>([]);
  const [currentPendingUpdate, setCurrentPendingUpdate] = useState<import("../../types").PendingUpdate | null>(null);

  // Fetch pending updates (forced quizzes)
  useEffect(() => {
    if (isManagerOrOwner || isVinfast) return; // managers/owners/vinfast don't take quizzes
    const fetchPending = async () => {
      try {
        const { pendingUpdateApi } = await import("../../services/api");
        const updates = await pendingUpdateApi.getPendingUpdates();
        if (updates && updates.length > 0) {
          setPendingUpdates(updates);
          setCurrentPendingUpdate(updates[0]);
        }
      } catch (err) {
        console.error("Failed to fetch pending updates:", err);
      }
    };
    fetchPending();
  }, [isManagerOrOwner, isVinfast]);

  useEffect(() => {
    if (!isVinfast) return;
    const fetchUnread = () => supportApi.getUnreadCount().then((r) => setUnreadCount(r.unread_count)).catch(() => undefined);
    fetchUnread();
    const interval = setInterval(fetchUnread, 30000);
    return () => clearInterval(interval);
  }, [isVinfast]);

  const initials = user?.full_name?.split(" ").slice(-2).map((word) => word[0]).join("").toUpperCase() || "VF";
  const closeMobileNav = () => setMobileNavOpen(false);
  const navClass = ({ isActive }: { isActive: boolean }) => `vf-nav-item ${isActive ? "active" : ""}`;

  const handlePendingUpdateCompleted = (updateId: number) => {
    setPendingUpdates((prev) => {
      const next = prev.filter(u => u.id !== updateId);
      if (next.length > 0) {
        setCurrentPendingUpdate(next[0]);
      } else {
        setCurrentPendingUpdate(null);
      }
      return next;
    });
  };

  return (
    <div className="vf-shell">
      <button className="vf-mobile-menu" onClick={() => setMobileNavOpen((open) => !open)} aria-label="Mở trình đơn">
        {mobileNavOpen ? <X size={22} /> : <Menu size={22} />}
      </button>

      <aside className={`vf-sidebar ${mobileNavOpen ? "mobile-open" : ""}`}>
        <NavLink to="/onboarding" className="vf-sidebar-brand" onClick={closeMobileNav}>
          <strong>VF AI Onboarding</strong>
        </NavLink>

        <div className="vf-profile-block">
          <div className="vf-profile-avatar" title={user?.full_name}>{initials}</div>
          <div>
            <strong>{user?.full_name}</strong>
            <span>{user ? ROLE_LABELS[user.role] : ""}</span>
          </div>
        </div>

        <nav className="vf-nav" onClick={closeMobileNav}>
          {!isVinfast && !isOwner && <NavLink to="/onboarding" className={navClass}><ClipboardList size={20} /><span>Lộ trình học tập</span></NavLink>}
          {(isVinfast || isOwner) && <NavLink to="/files" className={navClass}><Upload size={20} /><span>Tài liệu</span></NavLink>}
          {isManagerOrOwner && <NavLink to="/progress" className={navClass}><ChartNoAxesColumnIncreasing size={20} /><span>Tiến độ đội ngũ</span></NavLink>}
          
          {isVinfast ? (
            <NavLink to="/support" className={navClass}><CircleHelp size={20} /><span>Hộp thư hỗ trợ</span>{unreadCount > 0 && <b className="vf-nav-badge">{unreadCount}</b>}</NavLink>
          ) : (
            <button className="vf-nav-item" onClick={() => setShowSupportModal(true)}><CircleHelp size={20} /><span>Gửi hỗ trợ</span></button>
          )}
          
          {isOwner && <NavLink to="/invite" className={navClass}><UserPlus size={20} /><span>Mời thành viên</span></NavLink>}
        </nav>

        <div className="vf-sidebar-footer">
          <button className="vf-nav-item vf-sidebar-logout" onClick={() => { logout(); navigate("/login"); }}><LogOut size={20} /><span>Đăng xuất</span></button>
        </div>
      </aside>

      {mobileNavOpen && <button className="vf-nav-scrim" onClick={closeMobileNav} aria-label="Đóng trình đơn" />}
      <main className="vf-page-content"><Outlet /></main>
      {!isVinfast && <ChatWidget />}
      
      {showSupportModal && <SupportModal onClose={() => setShowSupportModal(false)} />}

      {/* Pending Update forced Quiz Modal */}
      {currentPendingUpdate && (
        <PendingQuizModal 
          pendingUpdate={currentPendingUpdate} 
          onCompleted={handlePendingUpdateCompleted}
        />
      )}
    </div>
  );
}
