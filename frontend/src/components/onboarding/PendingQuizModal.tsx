import { useState } from "react";
import type { PendingUpdate } from "../../types";
import { pendingUpdateApi } from "../../services/api";

interface Props {
  pendingUpdate: PendingUpdate;
  onCompleted: (updateId: number) => void;
}

export default function PendingQuizModal({ pendingUpdate, onCompleted }: Props) {
  const { step } = pendingUpdate;
  const questions = step.quiz || [];
  
  const [currentQ, setCurrentQ] = useState(0);
  const [selectedOpt, setSelectedOpt] = useState<number | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!questions || questions.length === 0) {
    // If somehow there are no questions, just mark it as complete
    pendingUpdateApi.completePendingUpdate(pendingUpdate.id)
      .then(() => onCompleted(pendingUpdate.id))
      .catch(console.error);
    return null;
  }

  const question = questions[currentQ];

  const handleSelect = (idx: number) => {
    if (showResult) return;
    setSelectedOpt(idx);
  };

  const handleCheck = () => {
    if (selectedOpt === null) return;
    setShowResult(true);
  };

  const handleNext = async () => {
    if (selectedOpt !== question.correctIndex) {
      // Re-try this question
      setSelectedOpt(null);
      setShowResult(false);
      return;
    }

    if (currentQ < questions.length - 1) {
      // Next question
      setCurrentQ((prev) => prev + 1);
      setSelectedOpt(null);
      setShowResult(false);
    } else {
      // Finish
      try {
        setIsSubmitting(true);
        await pendingUpdateApi.completePendingUpdate(pendingUpdate.id);
        onCompleted(pendingUpdate.id);
      } catch (err) {
        console.error("Failed to complete pending update", err);
      } finally {
        setIsSubmitting(false);
      }
    }
  };

  return (
    <div className="vf-modal-overlay z-50 fixed inset-0 bg-black/60 flex items-center justify-center p-4">
      <div className="vf-modal-content bg-white rounded-xl shadow-2xl w-full" style={{ maxWidth: "600px" }}>
        <div className="vf-modal-header p-6 border-b border-gray-100">
          <h2 className="vf-modal-title text-2xl font-bold text-red-600">
            Tài liệu mới cập nhật: {step.title}
          </h2>
          <p className="vf-modal-subtitle mt-2 text-gray-600 text-sm">
            Quản lý vừa tải lên tài liệu mới cho bài học này. Bạn cần hoàn thành bài kiểm tra để tiếp tục.
          </p>
        </div>

        <div className="vf-modal-body p-6">
          <div className="mb-4 text-sm font-medium text-gray-500">
            Câu {currentQ + 1} / {questions.length}
          </div>
          
          <h3 className="text-xl font-semibold mb-6 text-gray-800">{question.question}</h3>
          
          <div className="space-y-3 mb-6">
            {question.options.map((opt, idx) => {
              let btnClass = "w-full text-left p-4 rounded-lg border-2 transition-all ";
              if (showResult) {
                if (idx === question.correctIndex) {
                  btnClass += "border-green-500 bg-green-50 text-green-700";
                } else if (idx === selectedOpt) {
                  btnClass += "border-red-500 bg-red-50 text-red-700";
                } else {
                  btnClass += "border-gray-200 opacity-50 text-gray-500";
                }
              } else {
                if (idx === selectedOpt) {
                  btnClass += "border-blue-500 bg-blue-50 text-blue-700";
                } else {
                  btnClass += "border-gray-200 hover:border-blue-300 hover:bg-blue-50/50 text-gray-700";
                }
              }

              return (
                <button
                  key={idx}
                  className={btnClass}
                  onClick={() => handleSelect(idx)}
                  disabled={showResult}
                >
                  <span className="font-bold mr-3">{String.fromCharCode(65 + idx)}.</span>
                  {opt}
                </button>
              );
            })}
          </div>

          {showResult && (
            <div className={`p-4 rounded-lg mb-2 ${selectedOpt === question.correctIndex ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
              <p className={`font-bold mb-1 ${selectedOpt === question.correctIndex ? 'text-green-800' : 'text-red-800'}`}>
                {selectedOpt === question.correctIndex ? "Chính xác!" : "Chưa chính xác"}
              </p>
              <p className="text-sm text-gray-700">{question.explanation}</p>
            </div>
          )}
        </div>

        <div className="vf-modal-footer p-6 border-t border-gray-100 flex justify-end bg-gray-50 rounded-b-xl">
          {!showResult ? (
            <button
              className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium disabled:opacity-50 transition-colors shadow-sm"
              onClick={handleCheck}
              disabled={selectedOpt === null}
            >
              Kiểm tra
            </button>
          ) : (
            <button
              className={`px-6 py-2.5 text-white rounded-lg font-medium transition-colors shadow-sm ${
                isSubmitting ? 'bg-blue-400 cursor-not-allowed' :
                selectedOpt === question.correctIndex ? 'bg-blue-600 hover:bg-blue-700' : 'bg-red-600 hover:bg-red-700'
              }`}
              onClick={handleNext}
              disabled={isSubmitting}
            >
              {isSubmitting ? "Đang xử lý..." : selectedOpt === question.correctIndex ? (currentQ < questions.length - 1 ? "Câu tiếp theo" : "Hoàn thành") : "Thử lại"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
