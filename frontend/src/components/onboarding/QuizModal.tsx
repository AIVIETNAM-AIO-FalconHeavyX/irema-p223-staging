import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, Check, RotateCcw, Trophy, X } from "lucide-react";

export interface QuizQuestion {
  id: number;
  question: string;
  options: string[];
  correctIndex: number;
  explanation: string;
}

interface QuizModalProps {
  isOpen: boolean;
  stepTitle: string;
  questions: QuizQuestion[];
  onClose: () => void;
  onSuccess: () => void;
  passingScore?: number;
  onResult?: (score: number, passed: boolean) => void | Promise<void>;
}

export default function QuizModal({
  isOpen,
  stepTitle,
  questions,
  onClose,
  onSuccess,
  passingScore = 80,
  onResult,
}: QuizModalProps) {
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, number>>({});
  const [submitted, setSubmitted] = useState(false);
  const [showCompletion, setShowCompletion] = useState(false);
  const [saving, setSaving] = useState(false);
  const [shuffledQuestions, setShuffledQuestions] = useState<QuizQuestion[]>([]);

  useEffect(() => {
    if (isOpen) {
      // Shuffle options when modal opens
      setShuffledQuestions(
        questions.map((q) => {
          const optionsWithMeta = q.options.map((opt, idx) => ({
            text: opt,
            isCorrect: idx === q.correctIndex,
          }));
          for (let i = optionsWithMeta.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [optionsWithMeta[i], optionsWithMeta[j]] = [
              optionsWithMeta[j],
              optionsWithMeta[i],
            ];
          }
          return {
            ...q,
            options: optionsWithMeta.map((o) => o.text),
            correctIndex: optionsWithMeta.findIndex((o) => o.isCorrect),
          };
        })
      );
      setSubmitted(false);
      setShowCompletion(false);
      setSelectedAnswers({});
      setSaving(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSelect = (questionId: number, optionIdx: number) => {
    if (submitted) return;
    setSelectedAnswers((prev) => ({ ...prev, [questionId]: optionIdx }));
  };

  const isComplete = shuffledQuestions.length > 0 && shuffledQuestions.every((q) => selectedAnswers[q.id] !== undefined);

  const correctCount = shuffledQuestions.filter(
    (q) => selectedAnswers[q.id] === q.correctIndex
  ).length;

  const score = shuffledQuestions.length ? Math.round((correctCount / shuffledQuestions.length) * 100) : 0;
  const isPassed = score >= passingScore;

  const handleSubmit = async () => {
    setSaving(true);
    setSubmitted(true);
    try {
      await onResult?.(score, isPassed);
    } finally {
      setSaving(false);
    }
  };

  const handleFinish = () => {
    if (isPassed) {
      setShowCompletion(true);
      return;
    }
    onClose();
  };

  const handleCompletionClose = () => {
    onSuccess();
    onClose();
  };

  return (
    <AnimatePresence>
      <div className="modal-backdrop">
        <motion.div
          className={`quiz-modal ${showCompletion ? "quiz-completion-modal" : ""}`}
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
        >
          {showCompletion ? (
            <div className="quiz-completion">
              <div className="quiz-completion-icon"><Trophy size={42} /></div>
              <span className="quiz-completion-eyebrow">HOÀN THÀNH MODULE</span>
              <h2>Chúc mừng, bạn đã hoàn thành!</h2>
              <p>{stepTitle}</p>
              <div className="quiz-completion-stats">
                <div><strong>{correctCount}/{shuffledQuestions.length}</strong><span>Câu trả lời đúng</span></div>
                <div><strong>{score}%</strong><span>Kết quả bài kiểm tra</span></div>
              </div>
              <button className="btn-primary" onClick={handleCompletionClose}>
                Tiếp tục lộ trình <ArrowRight size={18} />
              </button>
            </div>
          ) : (
            <>
              {/* Header */}
              <div className="modal-header">
                <div>
                  <span className="quiz-badge">BÀI KIỂM TRA</span>
                  <h2 className="modal-title">{stepTitle}</h2>
                </div>
                <button className="modal-close-btn" onClick={onClose} aria-label="Đóng"><X size={20} /></button>
              </div>

              {/* Body */}
              <div className="modal-body">
                {shuffledQuestions.map((q, idx) => {
                  const selected = selectedAnswers[q.id];
                  const isCorrect = selected === q.correctIndex;

                  return (
                    <div key={q.id} className="quiz-question-card">
                      <h4 className="q-title">
                        Câu {idx + 1}: {q.question}
                      </h4>

                      <div className="q-options">
                        {q.options.map((opt, optIdx) => {
                          let optionClass = "q-option";
                          if (selected === optIdx) optionClass += " selected";

                          if (submitted) {
                            if (optIdx === q.correctIndex) {
                              optionClass += " correct";
                            } else if (selected === optIdx) {
                              optionClass += " wrong";
                            }
                          }

                          return (
                            <button
                              key={optIdx}
                              className={optionClass}
                              onClick={() => handleSelect(q.id, optIdx)}
                            >
                              <span className="radio-dot">
                                {submitted && optIdx === q.correctIndex
                                  ? <Check size={16} />
                                  : submitted && selected === optIdx
                                  ? <X size={16} />
                                  : selected === optIdx
                                  ? "●"
                                  : "○"}
                              </span>
                              <span>{opt}</span>
                            </button>
                          );
                        })}
                      </div>

                      {submitted && (
                        <div
                          className={`q-explanation ${
                            isCorrect ? "correct-bg" : "wrong-bg"
                          }`}
                        >
                          <strong>{isCorrect ? "✅ Chính xác!" : "❌ Chưa đúng:"}</strong>{" "}
                          {q.explanation}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Footer */}
              <div className="modal-footer">
                {!submitted ? (
                  <button
                    className="btn-primary btn-full"
                    disabled={!isComplete}
                    onClick={handleSubmit}
                  >
                    Nộp bài & Kiểm tra →
                  </button>
                ) : (
                  <div className="quiz-result-bar">
                    <div className="result-text">
                      Kết quả: <strong>{correctCount}/{shuffledQuestions.length} câu đúng ({score}%)</strong>
                    </div>
                    <button className="btn-primary" onClick={handleFinish} disabled={saving}>
                      {isPassed
                        ? <><Check size={18} /> Hoàn tất module</>
                        : <><RotateCcw size={18} /> Đóng và làm lại</>}
                    </button>
                  </div>
                )}
              </div>
            </>
          )}
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
