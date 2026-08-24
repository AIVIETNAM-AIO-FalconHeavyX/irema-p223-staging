import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import api, { mediaUrl } from "../../services/api";
import type { OnboardingResource } from "../../types";

interface ResourceViewerModalProps {
  resource: OnboardingResource | null;
  onClose: () => void;
}

/** Đuôi file trình duyệt xem trực tiếp được; còn lại chỉ cho tải xuống. */
const VIDEO_EXTENSIONS = [".mp4", ".webm"];
const PDF_EXTENSION = ".pdf";

const extensionOf = (path: string): string => {
  const cleanPath = path.split("?")[0].split("#")[0];
  const dot = cleanPath.lastIndexOf(".");
  return dot === -1 ? "" : cleanPath.slice(dot).toLowerCase();
};

const OFFICE_LABELS: Record<string, string> = {
  ".docx": "Tài liệu Word",
  ".xlsx": "Bảng tính Excel",
  ".pptx": "Bài trình chiếu PowerPoint",
};

export default function ResourceViewerModal({ resource, onClose }: ResourceViewerModalProps) {
  const [pdfBlobUrl, setPdfBlobUrl] = useState<string | null>(null);
  const [loadingPdf, setLoadingPdf] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);

  const ext = resource ? extensionOf(resource.path) : "";
  const isVideo = VIDEO_EXTENSIONS.includes(ext);
  const isPdf = ext === PDF_EXTENSION;

  const rawViewUrl = resource ? mediaUrl(resource.path) : "";
  const downloadUrl = resource ? mediaUrl(resource.path, true) : "";

  // Nạp PDF dưới dạng Blob URL trong bộ nhớ để trình duyệt hiển thị trực tiếp 100% không bị tải xuống
  useEffect(() => {
    if (!resource || !isPdf || !rawViewUrl) {
      setPdfBlobUrl(null);
      return;
    }

    let isMounted = true;
    setLoadingPdf(true);
    setPdfError(null);

    api.get(rawViewUrl, { responseType: "blob" })
      .then((res) => {
        if (!isMounted) return;
        const blob = new Blob([res.data], { type: "application/pdf" });
        const objectUrl = URL.createObjectURL(blob);
        setPdfBlobUrl(objectUrl);
      })
      .catch((err) => {
        if (!isMounted) return;
        console.error("Lỗi xem trực tiếp PDF:", err);
        setPdfError("Không thể hiển thị bản xem trực tiếp. Bạn có thể sử dụng nút Tải xuống bên dưới.");
      })
      .finally(() => {
        if (isMounted) setLoadingPdf(false);
      });

    return () => {
      isMounted = false;
    };
  }, [resource?.path, isPdf, rawViewUrl]);

  // Giải phóng bộ nhớ Blob URL khi đổi file hoặc đóng Modal
  useEffect(() => {
    return () => {
      if (pdfBlobUrl) {
        URL.revokeObjectURL(pdfBlobUrl);
      }
    };
  }, [pdfBlobUrl]);

  if (!resource) return null;

  return (
    <AnimatePresence>
      <div className="modal-backdrop" onClick={onClose}>
        <motion.div
          className="resource-modal"
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="modal-header">
            <div>
              <span className="resource-badge">
                {isVideo ? "🎬 Video hướng dẫn" : isPdf ? "📄 Tài liệu PDF" : "📁 Tài liệu"}
              </span>
              <h2 className="modal-title">{resource.name}</h2>
            </div>
            <button className="modal-close-btn" onClick={onClose}>
              ✕
            </button>
          </div>

          <div className="modal-body resource-viewer-body">
            {isVideo && (
              <video className="resource-video" src={rawViewUrl} controls preload="metadata">
                Trình duyệt của bạn không hỗ trợ phát video.
              </video>
            )}

            {isPdf && (
              <div style={{ width: "100%", height: "85vh", position: "relative" }}>
                {loadingPdf && (
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", color: "#fff" }}>
                    <div className="loading-spinner" />
                    <p style={{ marginTop: 12, fontSize: 14 }}>Đang tải bản xem trực tiếp PDF...</p>
                  </div>
                )}
                {pdfError && (
                  <div className="resource-download-box">
                    <div className="resource-download-icon">⚠️</div>
                    <h3>{pdfError}</h3>
                    <a className="btn-primary" href={downloadUrl} download style={{ marginTop: 16 }}>
                      Tải xuống {resource.name}
                    </a>
                  </div>
                )}
                {pdfBlobUrl && !loadingPdf && (
                  <object
                    data={`${pdfBlobUrl}#toolbar=1&navpanes=0`}
                    type="application/pdf"
                    className="resource-pdf"
                    style={{ width: "100%", height: "85vh", border: "none" }}
                  >
                    <iframe
                      src={`${pdfBlobUrl}#toolbar=1&navpanes=0`}
                      className="resource-pdf"
                      title={resource.name}
                      style={{ width: "100%", height: "85vh", border: "none" }}
                    >
                      <p>Trình duyệt không hỗ trợ xem trực tiếp. <a href={downloadUrl} download>Tải về PDF tại đây</a>.</p>
                    </iframe>
                  </object>
                )}
              </div>
            )}

            {!isVideo && !isPdf && (
              <div className="resource-download-box">
                <div className="resource-download-icon">📥</div>
                <h3>{OFFICE_LABELS[ext] ?? "Tệp đính kèm"}</h3>
                <p>
                  Định dạng này ({ext.toUpperCase()}) không hỗ trợ xem trực tiếp trên trình duyệt. Bạn hãy tải về để xem bằng ứng dụng chuyên dụng.
                </p>
                <a className="btn-primary" href={downloadUrl} download style={{ marginTop: 16 }}>
                  Tải xuống {resource.meta || resource.name}
                </a>
              </div>
            )}
          </div>

          <div className="modal-footer resource-footer">
            <span className="resource-footer-meta">{resource.meta}</span>
            <div className="resource-footer-actions">
              <a className="btn-outline" href={downloadUrl} download>
                ⬇ Tải xuống
              </a>
              <button className="btn-primary" onClick={onClose}>
                Đóng
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
