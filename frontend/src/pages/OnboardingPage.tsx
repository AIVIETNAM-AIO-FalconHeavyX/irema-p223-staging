import { useEffect, useMemo, useState } from "react";
import { ArrowRight, CheckCircle2, CircleHelp, Clock3, Play } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { onboardingApi } from "../services/api";
import type { ModuleStatus, OnboardingStep } from "../types";
import { ROLE_LABELS } from "../types";
import {
  buildLearningModules,
  moduleResourceCount,
  type LearningModule,
} from "../utils/learningModules";

const progressFallback = (): ModuleStatus[] => [1, 2, 3].map((module_id) => ({
  module_id,
  unlocked: module_id === 1,
  completed: false,
  quiz_score: null,
  step_ids: [],
}));

export default function OnboardingPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [steps, setSteps] = useState<OnboardingStep[]>([]);
  const [moduleStatuses, setModuleStatuses] = useState<ModuleStatus[]>(progressFallback());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    Promise.all([onboardingApi.getSteps(), onboardingApi.getProgress()])
      .then(([stepData, progress]) => {
        if (cancelled) return;
        setSteps(stepData);
        setModuleStatuses(progress.modules || progressFallback());
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [user?.role]);

  const modules = useMemo(() => buildLearningModules(steps), [steps]);
  const moduleStatus = (module: LearningModule) => moduleStatuses.find((item) => item.module_id === module.id);
  const moduleIsComplete = (module: LearningModule) => Boolean(moduleStatus(module)?.completed);
  const moduleIsUnlocked = (module: LearningModule) => Boolean(moduleStatus(module)?.unlocked);
  const completedModules = modules.filter(moduleIsComplete).length;
  const progress = Math.round((completedModules / modules.length) * 100);
  const currentModuleIndex = modules.findIndex((module) => !moduleIsComplete(module));

  const openModule = (module: LearningModule) => {
    if (!moduleIsUnlocked(module)) return;
    const first = module.steps.flatMap((step) =>
      step.resources.map((resource) => ({ resource, step })),
    )[0];
    if (!first) return;
    const params = new URLSearchParams({
      module: String(module.id),
      step: String(first.step.id),
      path: first.resource.path,
    });
    navigate(`/resource?${params.toString()}`);
  };

  if (loading) {
    return <div className="loading-screen"><div className="loading-spinner" /><p>Đang tải lộ trình học tập...</p></div>;
  }

  return (
    <div className="vf-learning-page">
      <div className="vf-learning-heading">
        <h1>Lộ trình học tập</h1>
        <p>Nội dung dành cho <strong>{user ? ROLE_LABELS[user.role] : "vai trò của bạn"}</strong>, được tổ chức thành 3 module.</p>
      </div>

      <div className="vf-learning-layout">
        <section className="vf-learning-path">
          <div className="vf-section-head">
            <div><h2>Chương trình onboarding</h2><p>Chọn một module để mở không gian học tập và tài liệu liên quan.</p></div>
          </div>

          <div className="vf-module-list">
            {modules.map((module, index) => {
              const isDone = moduleIsComplete(module);
              const isUnlocked = moduleIsUnlocked(module);
              const isCurrent = index === currentModuleIndex;
              const resourceCount = moduleResourceCount(module);
              return (
                <button
                  key={module.id}
                  className={`vf-module-row vf-module-button ${isDone ? "done" : ""} ${isCurrent ? "current" : ""} ${!isUnlocked ? "locked" : ""}`}
                  onClick={() => openModule(module)}
                  disabled={resourceCount === 0 || !isUnlocked}
                >
                  {isDone ? <CheckCircle2 /> : isCurrent ? <span className="vf-play-box"><Play size={18} fill="currentColor" /></span> : <Clock3 />}
                  <span className="vf-module-copy">
                    <strong>{module.id}. {module.title}</strong>
                    <span>{module.description}</span>
                    <small>{resourceCount} tài liệu</small>
                  </span>
                  <span className="vf-module-action">
                    <b>{isDone ? "Hoàn thành" : isCurrent ? "Tiếp tục học" : "Bắt đầu"}</b>
                    <ArrowRight size={18} />
                  </span>
                </button>
              );
            })}
          </div>
        </section>

        <aside className="vf-dashboard-aside">
          <div className="vf-progress-summary">
            <h2>Tiến độ chung</h2>
            <div><strong>{progress}%</strong><span>hoàn thành</span></div>
            <div className="vf-progress-track"><i style={{ width: `${progress}%` }} /></div>
            <p>Đã hoàn thành {completedModules}/{modules.length} module trong lộ trình.</p>
          </div>
          <div className="vf-help-panel"><CircleHelp /><h2>Cần hỗ trợ?</h2><p>Trợ lý AI luôn sẵn sàng hỗ trợ trong quá trình học.</p></div>
        </aside>
      </div>
    </div>
  );
}
