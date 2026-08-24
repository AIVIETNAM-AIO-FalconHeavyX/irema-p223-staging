/**
 * FeedbackWidget — Widget ↑/−/↓ góc phải dưới mỗi AI response.
 *
 * - Ba nút: ↑ (Chính xác) | − (Phần đúng phần sai) | ↓ (Sai)
 * - Gửi POST /api/v1/feedback lên backend
 * - Lưu vào SQLite local để phân tích chất lượng RAG
 * - Hiển thị "Cảm ơn phản hồi!" sau khi submit
 */
import { useState } from "react";
import { chatApi } from "../../services/api";
import type { FeedbackPayload, RetrievedDocInfo } from "../../types";

interface FeedbackWidgetProps {
  query: string;
  response: string;
  intent?: string;
  retrievedDocs?: RetrievedDocInfo[];
}

type Rating = "up" | "neutral" | "down";

const BUTTONS: Array<{ rating: Rating; icon: string; label: string; activeClass: string }> = [
  { rating: "up", icon: "↑", label: "Chính xác", activeClass: "fb-btn--up" },
  { rating: "neutral", icon: "−", label: "Phần đúng phần sai", activeClass: "fb-btn--neutral" },
  { rating: "down", icon: "↓", label: "Sai / Không tìm thấy", activeClass: "fb-btn--down" },
];

export default function FeedbackWidget({
  query,
  response,
  intent,
  retrievedDocs = [],
}: FeedbackWidgetProps) {
  const [selected, setSelected] = useState<Rating | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleRate = async (rating: Rating) => {
    if (submitted || submitting) return;
    setSelected(rating);
    setSubmitting(true);

    const payload: FeedbackPayload = {
      query,
      response,
      intent,
      citations: retrievedDocs.map((d) => d.doc_name),
      rerank_scores: retrievedDocs.map((d) => d.rerank_score),
      rating,
    };

    try {
      await chatApi.submitFeedback(payload);
    } catch {
      // Silent fail — UX vẫn hiển thị "Cảm ơn"
    } finally {
      setSubmitting(false);
      setSubmitted(true);
    }
  };

  return (
    <div className="fb-widget">
      {submitted ? (
        <span className="fb-thanks">
          ✓ Cảm ơn phản hồi!
        </span>
      ) : (
        <>
          <span className="fb-label">Câu trả lời có đúng?</span>
          <div className="fb-buttons">
            {BUTTONS.map(({ rating, icon, label, activeClass }) => (
              <button
                key={rating}
                className={`fb-btn ${selected === rating ? activeClass : ""} ${submitting ? "fb-btn--disabled" : ""}`}
                title={label}
                onClick={() => handleRate(rating)}
                disabled={submitting}
                aria-label={label}
              >
                {icon}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
