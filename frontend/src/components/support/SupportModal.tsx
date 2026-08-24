import { useState, useRef } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { supportApi } from "../../services/api";

interface SupportModalProps {
  onClose: () => void;
}

export default function SupportModal({ onClose }: SupportModalProps) {
  const { user } = useAuth();
  const [agencyId, setAgencyId] = useState(user?.agency_id || "");
  const [description, setDescription] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!agencyId.trim() || !description.trim()) {
      setError("Vui lòng điền đầy đủ Mã đại lý và Mô tả vấn đề.");
      return;
    }
    if (description.trim().length < 10) {
      setError("Mô tả vấn đề cần ít nhất 10 ký tự.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("agency_id", agencyId.trim());
      formData.append("description", description.trim());
      if (file) formData.append("file", file);

      await supportApi.createTicket(formData);
      setSuccess(true);
      setTimeout(() => onClose(), 2000);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e?.response?.data?.detail || "Gửi yêu cầu thất bại. Vui lòng thử lại.");
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) {
      if (selected.size > 10 * 1024 * 1024) {
        setError("File không được vượt quá 10MB.");
        return;
      }
      setFile(selected);
      setError("");
    }
  };

  return (
    <div className="support-modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="support-modal">
        {/* Header */}
        <div className="support-modal-header">
          <div className="support-modal-title-row">
            <h2 className="support-modal-title">Gửi yêu cầu hỗ trợ</h2>
          </div>
          <button className="support-modal-close" onClick={onClose} aria-label="Đóng">✕</button>
        </div>

        {success ? (
          <div className="support-modal-success">
            <div className="support-success-icon">✅</div>
            <h3>Đã gửi thành công!</h3>
            <p>Quản lý sẽ xem xét và phản hồi yêu cầu của bạn sớm nhất.</p>
          </div>
        ) : (
          <form className="support-modal-form" onSubmit={handleSubmit}>
            {/* Agency ID */}
            <div className="support-form-group">
              <label className="support-form-label" htmlFor="support-agency-id">
                Mã đại lý <span className="support-required">*</span>
              </label>
              <input
                id="support-agency-id"
                type="text"
                className="support-form-input"
                placeholder="VD: VF-HN-001"
                value={agencyId}
                onChange={(e) => setAgencyId(e.target.value)}
                disabled={loading}
                maxLength={100}
              />
            </div>

            {/* Description */}
            <div className="support-form-group">
              <label className="support-form-label" htmlFor="support-description">
                Mô tả vấn đề <span className="support-required">*</span>
              </label>
              <textarea
                id="support-description"
                className="support-form-textarea"
                placeholder="Mô tả chi tiết vấn đề bạn gặp phải..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={loading}
                rows={5}
                maxLength={2000}
              />
              <span className="support-char-count">{description.length}/2000</span>
            </div>

            {/* File Upload */}
            <div className="support-form-group">
              <label className="support-form-label">Đính kèm ảnh / file (tuỳ chọn)</label>
              <div
                className={`support-file-zone ${file ? "has-file" : ""}`}
                onClick={() => fileInputRef.current?.click()}
              >
                {file ? (
                  <div className="support-file-info">
                    <span className="support-file-name">📎 {file.name}</span>
                    <button
                      type="button"
                      className="support-file-remove"
                      onClick={(e) => { e.stopPropagation(); setFile(null); if (fileInputRef.current) fileInputRef.current.value = ""; }}
                    >
                      ✕
                    </button>
                  </div>
                ) : (
                  <div className="support-file-placeholder">
                    <span>📂</span>
                    <span>Click để chọn file hoặc kéo thả vào đây</span>
                    <span className="support-file-hint">PNG, JPG, PDF tối đa 10MB</span>
                  </div>
                )}
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*,.pdf,.doc,.docx"
                style={{ display: "none" }}
                onChange={handleFileChange}
              />
            </div>

            {error && <div className="support-form-error">⚠️ {error}</div>}

            <div className="support-form-actions">
              <button type="button" className="support-btn-cancel" onClick={onClose} disabled={loading}>
                Huỷ
              </button>
              <button type="submit" className="support-btn-submit" disabled={loading}>
                {loading ? (
                  <span className="support-loading">⏳ Đang gửi...</span>
                ) : (
                  "Gửi yêu cầu"
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
