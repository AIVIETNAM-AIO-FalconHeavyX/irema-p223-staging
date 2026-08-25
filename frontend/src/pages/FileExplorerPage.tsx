import { useState, useEffect, useRef } from "react";
import { Folder, File as FileIcon, Upload, Trash2, ChevronRight, ExternalLink, RefreshCw, CheckCircle, AlertCircle } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { mediaUrl } from "../services/api";

const API_BASE_URL = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");
const backendUrl = (path: string) => `${API_BASE_URL}${path}`;

interface FileItem {
  name: string;
  path: string;
  is_dir: boolean;
  size: number;
  last_modified: string | null;
}

const VALID_ROLES = [
  { value: "auto", label: "Tự động (theo thư mục)" },
  { value: "all", label: "Tất cả nhân viên" },
  { value: "accountant", label: "Kế toán" },
  { value: "sale", label: "Sales" },
  { value: "technician", label: "Kỹ thuật viên" },
  { value: "manager", label: "Quản lý" },
  { value: "owner", label: "Chủ đại lý" },
];

function formatErrorMsg(detail: any): string {
  if (!detail) return "Lỗi không xác định";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((d: any) => (typeof d === "object" && d.msg ? d.msg : JSON.stringify(d))).join("; ");
  }
  if (typeof detail === "object") {
    return detail.msg || JSON.stringify(detail);
  }
  return String(detail);
}

export default function FileExplorerPage() {
  const { user } = useAuth();
  const [currentPrefix, setCurrentPrefix] = useState<string>("");
  const [items, setItems] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Upload state
  const [targetRole, setTargetRole] = useState<string>("auto");
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadResults, setUploadResults] = useState<{ name: string; status: "success" | "error"; msg: string }[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ChromaDB re-index state
  const [reindexStatus, setReindexStatus] = useState<"idle" | "running" | "done" | "error">("idle");
  const [reindexMsg, setReindexMsg] = useState<string>("");
  const [syncFailures, setSyncFailures] = useState<{ s3_key: string; error_message: string | null }[]>([]);
  const pollRef = useRef<number | null>(null);

  const isVinfast = user?.role === "vinfast";

  const fetchItems = async (prefix: string) => {
    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem("vf_access_token");
      const res = await fetch(backendUrl(`/api/v1/s3-manager/explore?prefix=${encodeURIComponent(prefix)}`), {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Không thể tải danh sách tài liệu");
      const data = await res.json();
      setItems(data.items);
      setCurrentPrefix(data.prefix);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchItems(currentPrefix); }, []);

  // Poll reindex status
  const startPollingReindex = () => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = window.setInterval(async () => {
      try {
        const token = localStorage.getItem("vf_access_token");
        const res = await fetch(backendUrl("/api/v1/s3-manager/sync/status"), {
          headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await res.json();
        setSyncFailures(data.failures || []);
        if (["completed", "dry_run", "failed"].includes(data.status)) {
          setReindexStatus(data.status === "failed" ? "error" : "done");
          setReindexMsg("✅ Chatbot đã được cập nhật thành công!");
          clearInterval(pollRef.current!);
          pollRef.current = null;
        }
      } catch { /* ignore */ }
    }, 4000);
  };

  const handleReindex = async () => {
    try {
      setReindexStatus("running");
      setReindexMsg("Đang cập nhật chatbot... (mất 2-5 phút)");
      const token = localStorage.getItem("vf_access_token");
      const res = await fetch(backendUrl("/api/v1/s3-manager/sync"), {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ dry_run: false })
      });
      const data = await res.json();
      if (!res.ok) {
        setReindexStatus("error");
        setReindexMsg(data.detail || "Không thể bắt đầu đồng bộ");
        return;
      }
      startPollingReindex();
    } catch (err: any) {
      setReindexStatus("error");
      setReindexMsg("Lỗi kết nối server.");
    }
  };

  const handleRetryFailed = async () => {
    const token = localStorage.getItem("vf_access_token");
    const res = await fetch(backendUrl("/api/v1/s3-manager/retry-failed"), {
      method: "POST",
      headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    const data = await res.json();
    if (!res.ok) {
      setReindexStatus("error");
      setReindexMsg(data.detail || "Retry failed");
      return;
    }
    setSyncFailures([]);
    setReindexStatus("running");
    setReindexMsg(`Retry queued for ${data.requeued || 0} document(s).`);
    startPollingReindex();
  };

  const handleUploadFiles = async (files: File[]) => {
    if (!isVinfast || files.length === 0) return;

    // Kiểm tra file trùng tên trong thư mục hiện tại
    const existingNames = items.filter(i => !i.is_dir).map(i => i.name);
    const duplicates = files.filter(f => existingNames.includes(f.name));
    if (duplicates.length > 0) {
      const names = duplicates.map(f => f.name).join(", ");
      if (!confirm(`File sau đã tồn tại:\n${names}\n\nBạn có muốn ghi đè không? Nhấn OK để tiếp tục, Cancel để huỷ.`)) {
        return;
      }
    }

    setUploading(true);
    setUploadResults([]);
    const results: typeof uploadResults = [];

    for (const file of files) {
      try {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("target_folder", currentPrefix);
        formData.append("target_role", targetRole);

        const token = localStorage.getItem("vf_access_token");
        const res = await fetch(backendUrl("/api/v1/s3-manager/upload-direct"), {
          method: "POST",
          headers: { "Authorization": `Bearer ${token}` },
          body: formData
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: "Lỗi không xác định" }));
          results.push({ name: file.name, status: "error", msg: formatErrorMsg(err.detail) });
        } else {
          const data = await res.json();
          results.push({ name: file.name, status: "success", msg: data.message || "Upload thành công" });
        }
      } catch (err: any) {
        results.push({ name: file.name, status: "error", msg: formatErrorMsg(err.message) });
      }
      setUploadResults([...results]);
    }

    setUploading(false);
    fetchItems(currentPrefix);
    // Sau khi upload xong, tự động trigger reindex
    if (results.some(r => r.status === "success")) {
      setTimeout(() => handleReindex(), 1000);
    }
  };

  const handleDeleteClick = async (path: string) => {
    if (!isVinfast) return;
    if (!confirm(`Bạn có chắc muốn xoá file: ${path}?\nHành động này không thể hoàn tác.`)) return;

    try {
      setLoading(true);
      const token = localStorage.getItem("vf_access_token");
      const res = await fetch(backendUrl(`/api/v1/s3-manager/delete?object_key=${encodeURIComponent(path)}`), {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Lỗi khi xoá file");
      fetchItems(currentPrefix);
      // Tự động trigger reindex sau khi xoá
      setTimeout(() => handleReindex(), 500);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const parts = currentPrefix.split("/").filter(p => p);

  return (
    <div className="vf-container">
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20, flexWrap: "wrap", gap: 12 }}>
        <div>
          <h1 className="vf-page-title">Kho Tài Liệu (MinIO)</h1>
          <p className="vf-page-subtitle">Duyệt và quản lý tài liệu lưu trữ trên hệ thống</p>
        </div>

        {isVinfast && (
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
            {/* Dropdown chọn role */}
            <select
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
              style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid #cbd5e1", fontSize: 14, background: "white" }}
              title="Tài liệu này dành cho role nào?"
            >
              {VALID_ROLES.map(r => (
                <option key={r.value} value={r.value}>{r.label}</option>
              ))}
            </select>

            {/* Nút Upload (nhiều file) */}
            <button
              className="vf-btn vf-btn-primary"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
            >
              <Upload size={18} />
              <span>{uploading ? `Đang upload...` : "Tải lên"}</span>
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.mp4,.webm"
              multiple
              style={{ display: "none" }}
              onChange={(e) => {
                const files = Array.from(e.target.files || []);
                e.target.value = "";
                handleUploadFiles(files);
              }}
            />

            {/* Nút Cập nhật Chatbot */}
            <button
              className="vf-btn"
              onClick={handleReindex}
              disabled={reindexStatus === "running"}
              style={{
                display: "flex", alignItems: "center", gap: 8,
                background: reindexStatus === "done" ? "#dcfce7" : reindexStatus === "running" ? "#fef3c7" : "#f1f5f9",
                color: reindexStatus === "done" ? "#166534" : reindexStatus === "running" ? "#92400e" : "#334155",
                border: "1px solid #e2e8f0", padding: "8px 16px", borderRadius: 8, cursor: reindexStatus === "running" ? "not-allowed" : "pointer"
              }}
              title="Đồng bộ tài liệu mới vào chatbot AI (ChromaDB)"
            >
              {reindexStatus === "done" ? <CheckCircle size={16} /> : reindexStatus === "error" ? <AlertCircle size={16} /> : <RefreshCw size={16} className={reindexStatus === "running" ? "spin" : ""} />}
              <span>{reindexStatus === "running" ? "Đang cập nhật..." : "Cập nhật Chatbot"}</span>
            </button>
          </div>
        )}
      </div>

      {/* Reindex status banner */}
      {reindexMsg && (
        <div style={{
          marginBottom: 16, padding: "10px 16px", borderRadius: 8,
          background: reindexStatus === "done" ? "#dcfce7" : reindexStatus === "error" ? "#fef2f2" : "#fef3c7",
          border: `1px solid ${reindexStatus === "done" ? "#86efac" : reindexStatus === "error" ? "#fca5a5" : "#fde68a"}`,
          fontSize: 14, color: "#374151"
        }}>
          {reindexMsg}
        </div>
      )}

      {isVinfast && syncFailures.length > 0 && (
        <div style={{ marginBottom: 16, padding: "10px 16px", borderRadius: 8, background: "#fef2f2", border: "1px solid #fca5a5" }}>
          <strong style={{ fontSize: 14 }}>Failed documents ({syncFailures.length})</strong>
          <ul style={{ margin: "8px 0", paddingLeft: 20, fontSize: 13 }}>
            {syncFailures.map((failure) => <li key={failure.s3_key}>{failure.s3_key} — {failure.error_message || "Unknown error"}</li>)}
          </ul>
          <button className="vf-btn" onClick={handleRetryFailed}>Retry failed</button>
        </div>
      )}

      {/* Upload results */}
      {uploadResults.length > 0 && (
        <div style={{ marginBottom: 16, padding: "10px 16px", borderRadius: 8, background: "#f8fafc", border: "1px solid #e2e8f0" }}>
          <strong style={{ fontSize: 14 }}>Kết quả upload ({uploadResults.filter(r => r.status === "success").length}/{uploadResults.length} thành công):</strong>
          <ul style={{ margin: "8px 0 0", padding: "0 0 0 20px", fontSize: 13 }}>
            {uploadResults.map((r, i) => (
              <li key={i} style={{ color: r.status === "success" ? "#166534" : "#dc2626" }}>
                [{r.status === "success" ? "Thành công" : "Lỗi"}] {r.name} — {r.msg}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Breadcrumb */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 20, fontSize: "14px", background: "white", padding: "12px 16px", borderRadius: 8, border: "1px solid #e2e8f0" }}>
        <button onClick={() => fetchItems("")} style={{ background: "none", border: "none", color: "#1e6fb5", cursor: "pointer", fontWeight: currentPrefix === "" ? "bold" : "normal" }}>
          Gốc
        </button>
        {parts.map((part, index) => (
          <div key={index} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <ChevronRight size={14} color="#64748b" />
            <button
              onClick={() => fetchItems(parts.slice(0, index + 1).join("/") + "/")}
              style={{ background: "none", border: "none", color: "#1e6fb5", cursor: "pointer", fontWeight: index === parts.length - 1 ? "bold" : "normal" }}
            >
              {part}
            </button>
          </div>
        ))}
      </div>

      {error && <div style={{ color: "red", marginBottom: 20 }}>{error}</div>}

      {/* File table */}
      <div style={{ background: "white", borderRadius: 8, border: "1px solid #e2e8f0", overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "14px" }}>
          <thead>
            <tr style={{ background: "#f8fafc", borderBottom: "1px solid #e2e8f0" }}>
              <th style={{ padding: "12px 16px", fontWeight: 600, color: "#475569" }}>Tên</th>
              <th style={{ padding: "12px 16px", fontWeight: 600, color: "#475569" }}>Kích thước</th>
              <th style={{ padding: "12px 16px", fontWeight: 600, color: "#475569" }}>Lần sửa đổi</th>
              <th style={{ padding: "12px 16px", fontWeight: 600, color: "#475569", textAlign: "right" }}>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={4} style={{ padding: 20, textAlign: "center" }}>Đang tải...</td></tr>
            ) : items.length === 0 ? (
              <tr><td colSpan={4} style={{ padding: 20, textAlign: "center", color: "#64748b" }}>Thư mục trống</td></tr>
            ) : (
              items.map((item, idx) => (
                <tr key={idx} style={{ borderBottom: "1px solid #e2e8f0" }}>
                  <td style={{ padding: "12px 16px" }}>
                    {item.is_dir ? (
                      <button
                        onClick={() => fetchItems(item.path)}
                        style={{ display: "flex", alignItems: "center", gap: 8, background: "none", border: "none", color: "#1e6fb5", cursor: "pointer", fontWeight: 500 }}
                      >
                        <Folder size={18} fill="#bfdbfe" color="#3b82f6" />
                        {item.name}
                      </button>
                    ) : (
                      <div style={{ display: "flex", alignItems: "center", gap: 8, color: "#334155" }}>
                        <FileIcon size={18} color="#64748b" />
                        <a href={mediaUrl(`s3://${item.path}`)} target="_blank" rel="noopener noreferrer"
                          style={{ color: "#1e6fb5", textDecoration: "none" }}>
                          {item.name}
                        </a>
                      </div>
                    )}
                  </td>
                  <td style={{ padding: "12px 16px", color: "#64748b" }}>{item.is_dir ? "-" : formatSize(item.size)}</td>
                  <td style={{ padding: "12px 16px", color: "#64748b" }}>
                    {item.last_modified ? new Date(item.last_modified).toLocaleString("vi-VN") : "-"}
                  </td>
                  <td style={{ padding: "12px 16px", textAlign: "right" }}>
                    {!item.is_dir && (
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 12 }}>
                        <a href={mediaUrl(`s3://${item.path}`)} target="_blank" rel="noopener noreferrer"
                          style={{ color: "#3b82f6", cursor: "pointer", display: "flex" }} title="Mở file">
                          <ExternalLink size={16} />
                        </a>
                        {isVinfast && (
                          <button
                            onClick={() => handleDeleteClick(item.path)}
                            style={{ background: "none", border: "none", color: "#ef4444", cursor: "pointer", padding: 0, display: "flex" }}
                            title="Xoá file"
                          >
                            <Trash2 size={16} />
                          </button>
                        )}
                      </div>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
