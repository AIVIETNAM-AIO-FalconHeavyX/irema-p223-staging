import { useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  CircleHelp,
  FileText,
  LogOut,
  PlayCircle,
} from "lucide-react";
import { useNavigate, useSearchParams } from "react-router-dom";
import ChatWidget from "../components/chat/ChatWidget";
import QuizModal, { type QuizQuestion } from "../components/onboarding/QuizModal";
import { useAuth } from "../contexts/AuthContext";
import { mediaUrl, onboardingApi } from "../services/api";
import { ROLE_LABELS, type ModuleStatus, type OnboardingResource, type OnboardingStep } from "../types";
import { buildLearningModules, type LearningModule } from "../utils/learningModules";

type CourseResource = OnboardingResource & { step: OnboardingStep; module: LearningModule };

const moduleStatusFallback = (): ModuleStatus[] => [1, 2, 3].map((module_id) => ({
  module_id, unlocked: module_id === 1, completed: false, quiz_score: null, step_ids: [],
}));

function viewerUrl(item: CourseResource) {
  const params = new URLSearchParams({ module: String(item.module.id), step: String(item.step.id), path: item.path });
  return `/resource?${params.toString()}`;
}

export default function CourseViewerPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [steps, setSteps] = useState<OnboardingStep[]>([]);
  const [completedIds, setCompletedIds] = useState<Set<number>>(new Set());
  const [completedSectionIds, setCompletedSectionIds] = useState<Set<string>>(new Set());
  const [moduleStatuses, setModuleStatuses] = useState<ModuleStatus[]>(moduleStatusFallback());
  const [loading, setLoading] = useState(true);
  const [documentUrl, setDocumentUrl] = useState<string | null>(null);
  const [documentError, setDocumentError] = useState(false);
  const [quizOpen, setQuizOpen] = useState(false);

  useEffect(() => {
    Promise.all([onboardingApi.getSteps(), onboardingApi.getProgress()])
      .then(([stepData, progress]) => {
        setSteps(stepData);
        setCompletedIds(new Set(progress.completed_step_ids));
        setCompletedSectionIds(new Set(progress.completed_section_ids || []));
        setModuleStatuses(progress.modules || moduleStatusFallback());
      })
      .finally(() => setLoading(false));
  }, []);

  const modules = useMemo(() => buildLearningModules(steps), [steps]);
  const requestedPath = searchParams.get("path");
  const requestedStep = Number(searchParams.get("step"));
  const requestedModule = Number(searchParams.get("module"));
  const selectedModule = modules.find((module) => module.id === requestedModule)
    ?? modules.find((module) => module.steps.some((step) =>
      step.id === requestedStep && step.resources.some((resource) => resource.path === requestedPath),
    ))
    ?? modules[0];
  const resources = useMemo<CourseResource[]>(
    () => selectedModule
      ? selectedModule.steps.flatMap((step) =>
        step.resources.map((resource) => ({ ...resource, step, module: selectedModule })),
      )
      : [],
    [selectedModule],
  );
  const requestedIndex = resources.findIndex((item) =>
    item.path === requestedPath && (!requestedStep || item.step.id === requestedStep),
  );
  const activeIndex = requestedIndex >= 0 ? requestedIndex : 0;
  const active = resources[activeIndex];
  const selectedStatus = selectedModule ? moduleStatuses.find((item) => item.module_id === selectedModule.id) : undefined;
  const moduleUnlocked = Boolean(selectedStatus?.unlocked);
  const quizScore = selectedStatus?.quiz_score ?? null;
  const moduleQuestions: QuizQuestion[] = useMemo(
    () => selectedModule ? selectedModule.steps.flatMap((step) => step.quiz.map((q) => ({ ...q, id: step.id * 1000 + q.id }))).slice(0, 10) : [],
    [selectedModule],
  );
  const previous = resources[activeIndex - 1];
  const next = resources[activeIndex + 1];
  const initials = user?.full_name.split(" ").slice(-2).map((part) => part[0]).join("").toUpperCase() || "VF";
  const completedCount = modules.filter((module) =>
    module.steps.length > 0
      && module.steps.every((step) => completedIds.has(step.id))
      && Boolean(moduleStatuses.find((item) => item.module_id === module.id)?.completed),
  ).length;
  const progress = Math.round((completedCount / modules.length) * 100);
  const extension = active?.path.split(".").pop()?.toLowerCase() || "";
  const isPdf = extension === "pdf";
  const sourceUrl = active ? mediaUrl(active.path) : "";

  useEffect(() => {
    if (!loading && selectedModule && selectedStatus && !selectedStatus.unlocked) {
      navigate("/onboarding");
    }
  }, [loading, navigate, selectedModule, selectedStatus]);

  useEffect(() => {
    if (!isPdf || !sourceUrl) {
      setDocumentUrl(null);
      setDocumentError(false);
      return;
    }

    const controller = new AbortController();
    let objectUrl: string | null = null;
    setDocumentUrl(null);
    setDocumentError(false);

    fetch(sourceUrl, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Không thể tải PDF (${response.status})`);
        return response.arrayBuffer();
      })
      .then((buffer) => {
        objectUrl = URL.createObjectURL(new Blob([buffer], { type: "application/pdf" }));
        setDocumentUrl(objectUrl);
      })
      .catch((error) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setDocumentError(true);
      });

    return () => {
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [isPdf, sourceUrl]);

  const handleComplete = async () => {
    if (!active) return;
    if (active.section_id && !completedSectionIds.has(active.section_id)) {
      setCompletedSectionIds((current) => new Set([...current, active.section_id as string]));
      try {
        const result = await onboardingApi.completeSection(active.section_id);
        setCompletedIds(new Set(result.completed_step_ids));
        setCompletedSectionIds(new Set(result.completed_section_ids || []));
      } catch {
        // Keep optimistic section state when the network is temporarily unavailable.
      }
    } else if (!active.section_id && !completedIds.has(active.step.id)) {
      const result = await onboardingApi.completeStep(active.step.id);
      setCompletedIds(new Set(result.completed_step_ids));
    }
    if (next) navigate(viewerUrl(next));
    else navigate("/onboarding");
  };

  if (loading) {
    return <div className="loading-screen"><div className="loading-spinner" /><p>Đang tải nội dung khóa học...</p></div>;
  }

  if (!active) {
    return (
      <div className="vf-viewer-empty">
        <FileText size={38} />
        <h1>Không tìm thấy tài liệu</h1>
        <button className="btn-primary" onClick={() => navigate("/onboarding")}>Quay lại lộ trình</button>
      </div>
    );
  }

  return (
    <div className="vf-course-viewer">
      <header className="vf-course-topbar">
        <div className="vf-course-topbar-title">
          <button onClick={() => navigate("/onboarding")} aria-label="Quay lại lộ trình"><ArrowLeft size={21} /></button>
          <h5>QUAY LẠI LỘ TRÌNH</h5>
        </div>
        <div className="vf-course-user-actions">
          <div className="vf-course-progress"><span>Tiến độ: {completedCount}/{modules.length}</span><div><i style={{ width: `${progress}%` }} /></div></div>
        </div>
      </header>

      <aside className="vf-course-sidebar">
        <button className="vf-course-sidebar-brand" onClick={() => navigate("/onboarding")}><strong>VF AI Onboarding</strong></button>
        <div className="vf-course-sidebar-heading">
          <h4>Module {active.module.id}: {active.module.title}</h4>
          <p>{resources.length} tài liệu trong module</p>
        </div>
        <nav>
          <section>
            {active.module.steps.map((step, sectionIndex) => (
              <div className="vf-course-resource-section" key={step.id}>
                <div className="vf-course-resource-section-title">
                  <span>SECTION {sectionIndex + 1}</span>
                  <strong>{step.short_title || step.title}</strong>
                </div>
                {step.resources.map((resource) => {
                  const item: CourseResource = { ...resource, step, module: active.module };
                  const isActive = item.path === active.path && item.step.id === active.step.id;
                  return (
                    <button key={`${item.step.id}-${item.path}`} className={isActive ? "active" : ""} onClick={() => navigate(viewerUrl(item))} title={item.name}>
                      {item.type === "video" ? <PlayCircle size={19} /> : <FileText size={19} />}
                      <span>{item.name}</span>
                    </button>
                  );
                })}
              </div>
            ))}
            <button
              className={`vf-course-quiz-nav ${moduleUnlocked ? "ready" : "locked"} ${quizOpen ? "active" : ""}`}
              disabled={!moduleUnlocked}
              onClick={() => setQuizOpen(true)}
              title={moduleUnlocked ? "Mở quiz của module" : "Hoàn thành quiz module trước để mở module này"}
            >
              <CircleHelp size={19} />
              <span>Quiz module</span>
              <small>{quizScore !== null ? `${quizScore}%` : moduleUnlocked ? "Làm ngay" : "Đang khóa"}</small>
            </button>
          </section>
        </nav>
        <div className="vf-course-sidebar-account">
          <div className="vf-topbar-avatar" title={user?.full_name}>{initials}</div>
          <span><strong>{user?.full_name}</strong><small>{user ? ROLE_LABELS[user.role] : ""}</small></span>
          <button onClick={() => { logout(); navigate("/login"); }} title="Đăng xuất" aria-label="Đăng xuất"><LogOut size={19} /></button>
        </div>
      </aside>

      <main className="vf-course-content">
        <article>
          <span className="vf-course-kicker">{active.type === "video" ? "VIDEO ĐÀO TẠO" : "TÀI LIỆU HỌC TẬP"}</span>

          {active.type === "video" ? (
            <video className="vf-course-media" src={sourceUrl} controls preload="metadata">Trình duyệt không hỗ trợ phát video.</video>
          ) : isPdf && !documentError ? (
            documentUrl ? (
              <div className="vf-pdf-reader">
                <object className="vf-course-document" data={`${documentUrl}#toolbar=1&navpanes=0`} type="application/pdf">
                <div className="vf-course-download-card"><FileText size={38} /><h2>Không thể xem PDF trực tiếp</h2><a className="btn-primary" href={mediaUrl(active.path, true)} download>Tải tài liệu</a></div>
                </object>
              </div>
            ) : (
              <div className="vf-course-download-card vf-course-document-loading"><div className="loading-spinner" /><p>Đang tải tài liệu...</p></div>
            )
          ) : (
            <div className="vf-course-download-card"><FileText size={42} /><h2>{active.name}</h2><p>{isPdf ? "Không thể hiển thị tài liệu này trong trình duyệt." : `Định dạng ${extension.toUpperCase()} cần được mở bằng ứng dụng chuyên dụng.`}</p><a className="btn-primary" href={mediaUrl(active.path, true)} download>Tải tài liệu</a></div>
          )}

        </article>
      </main>

      <footer className="vf-course-footer">
        <button onClick={() => previous && navigate(viewerUrl(previous))} disabled={!previous}><ArrowLeft size={18} /> Bài trước</button>
        <button className="primary" onClick={handleComplete}>{next ? "Hoàn thành & Tiếp tục" : "Hoàn thành khóa học"}<ArrowRight size={18} /></button>
      </footer>

      <ChatWidget />
      <QuizModal isOpen={quizOpen} stepTitle={active.module.title} questions={moduleQuestions} passingScore={80} onClose={() => setQuizOpen(false)} onResult={async (score) => {
        const result = await onboardingApi.submitQuiz(active.module.id, score);
        setModuleStatuses(result.modules);
      }} onSuccess={async () => {
        setQuizOpen(false);
        navigate("/onboarding");
      }} />
    </div>
  );
}
