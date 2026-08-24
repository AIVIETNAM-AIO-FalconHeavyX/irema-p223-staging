import React, { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuth } from "../contexts/AuthContext";
import { ingestApi } from "../services/api";

const UploadDocumentPage: React.FC = () => {
  const { user } = useAuth();
  
  const [file, setFile] = useState<File | null>(null);
  const [role, setRole] = useState<string>("sale");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);
  const [result, setResult] = useState<any>(null);

  if (user?.role !== "owner") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
        <div className="bg-white p-8 rounded-xl shadow text-center max-w-sm">
          <h2 className="text-2xl font-bold text-red-600 mb-4">Truy cập bị từ chối</h2>
          <p className="text-gray-600 mb-6">Chỉ có Owner đại lý mới có quyền tải lên tài liệu mới.</p>
          <Link to="/" className="text-blue-600 hover:underline">Quay lại trang chủ</Link>
        </div>
      </div>
    );
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setMessage({ text: "Vui lòng chọn một file PDF.", type: "error" });
      return;
    }

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setMessage({ text: "Chỉ hỗ trợ file PDF.", type: "error" });
      return;
    }

    setLoading(true);
    setMessage(null);
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("role", role);

    try {
      const res = await ingestApi.uploadDocument(formData);
      setMessage({ text: res.message || "Upload thành công!", type: "success" });
      setResult(res);
      setFile(null);
      const fileInput = document.getElementById("file-upload") as HTMLInputElement;
      if (fileInput) fileInput.value = "";
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || "Có lỗi xảy ra khi upload.";
      setMessage({ text: errorMsg, type: "error" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-page">
      <motion.div 
        className="page-header"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 style={{ fontSize: "2.25rem", fontWeight: "700", marginBottom: "0.5rem" }}>Upload Tài Liệu Mới</h1>
        <p className="subtitle" style={{ fontSize: "1.1rem", color: "var(--ink-500)", marginTop: "1rem" }}>
          Tải lên tài liệu PDF. Hệ thống sẽ tự động cập nhật bài học và sinh câu hỏi trắc nghiệm AI.
        </p>
      </motion.div>

      <div style={{ maxWidth: "640px" }}>
        <motion.div 
          className="card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <form onSubmit={handleSubmit} className="auth-form">
            {message && (
              <div className={`alert ${message.type === 'success' ? 'alert-success' : 'alert-error'}`}>
                {message.type === 'success' ? '✅ ' : '⚠ '} {message.text}
              </div>
            )}

            <div className="form-group">
              <label htmlFor="role-select" style={{ fontSize: "1.1rem", fontWeight: "600", marginBottom: "0.5rem" }}>
                Vai trò áp dụng
              </label>
              <select
                id="role-select"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                disabled={loading}
                style={{ fontSize: "1rem", padding: "0.75rem 1rem" }}
              >
                <option value="sale">Nhân viên kinh doanh (Sales)</option>
                <option value="technician">Kỹ thuật viên</option>
                <option value="accountant">Kế toán</option>
                <option value="manager">Quản lý (Manager)</option>
              </select>
              <p style={{ marginTop: "0.5rem", fontSize: "0.95rem", color: "var(--ink-500)" }}>
                Tài liệu này sẽ được phân loại vào lộ trình đào tạo của vai trò tương ứng.
              </p>
            </div>

            <div className="form-group" style={{ marginTop: "1.5rem" }}>
              <label htmlFor="file-upload" style={{ fontSize: "1.1rem", fontWeight: "600", marginBottom: "0.5rem" }}>
                Tệp tài liệu (PDF)
              </label>
              <input
                id="file-upload"
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                disabled={loading}
                style={{ 
                  padding: "1rem", 
                  border: "2px dashed var(--line)", 
                  borderRadius: "var(--radius-md)",
                  cursor: "pointer",
                  fontSize: "1rem",
                  width: "100%"
                }}
              />
            </div>

            <button
              type="submit"
              className="btn-primary"
              disabled={loading}
              style={{ 
                marginTop: "2rem", 
                padding: "1rem", 
                fontSize: "1.1rem", 
                fontWeight: "600",
                width: "100%" 
              }}
            >
              {loading ? "🔄 Đang xử lý tài liệu AI..." : "Tải Lên & Xử Lý Tự Động"}
            </button>
          </form>

          {result && (
            <motion.div 
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              style={{ 
                marginTop: "2rem", 
                paddingTop: "1.5rem", 
                borderTop: "1px solid var(--line)",
                background: "var(--green-50)",
                margin: "2rem -1.5rem -1.5rem -1.5rem",
                padding: "1.5rem",
                borderRadius: "0 0 var(--radius-xl) var(--radius-xl)"
              }}
            >
              <h3 style={{ fontSize: "1.15rem", fontWeight: "700", color: "var(--ink-900)", marginBottom: "1rem" }}>
                ✨ Kết quả phân tích từ AI:
              </h3>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", background: "#fff", padding: "0.75rem 1rem", borderRadius: "8px", border: "1px solid var(--line)" }}>
                  <span style={{ fontWeight: "600", color: "var(--ink-700)" }}>Trạng thái bài học:</span> 
                  <span>{result.is_new_step ? "Tạo bài học mới" : "Cập nhật bài học hiện có"}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", background: "#fff", padding: "0.75rem 1rem", borderRadius: "8px", border: "1px solid var(--line)" }}>
                  <span style={{ fontWeight: "600", color: "var(--ink-700)" }}>Số câu hỏi Quiz đã sinh:</span> 
                  <span style={{ fontWeight: "700", color: "var(--green-700)" }}>{result.quiz_questions_generated} câu</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", background: "#fff", padding: "0.75rem 1rem", borderRadius: "8px", border: "1px solid var(--line)" }}>
                  <span style={{ fontWeight: "600", color: "var(--ink-700)" }}>Nhân viên cần cập nhật (nợ bài):</span> 
                  <span style={{ background: "#fef3c7", color: "#92400e", padding: "2px 8px", borderRadius: "99px", fontSize: "0.85rem", fontWeight: "700" }}>
                    {result.users_notified} nhân viên
                  </span>
                </div>
              </div>
            </motion.div>
          )}
        </motion.div>
      </div>
    </div>
  );
};

export default UploadDocumentPage;
