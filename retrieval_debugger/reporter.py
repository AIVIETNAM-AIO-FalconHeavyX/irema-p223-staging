"""Report generator for RAG retrieval testing & diagnostics."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from retrieval_debugger.logger import DebugSessionLogger


class DebugReporter:
    """Generates console table reports and Markdown summary artifacts."""

    def __init__(self, session_logger: DebugSessionLogger, output_dir: str = "retrieval_debugger/reports"):
        self.logger = session_logger
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def print_console_summary(self) -> None:
        """Print a formatted ANSI/Unicode summary table to the console."""
        logs = self.logger.logs
        total = len(logs)
        if total == 0:
            print("\n[Retrieval Debugger] Không có test case nào được thực thi.\n")
            return

        hit_1 = sum(1 for log in logs if log.diagnosis.get("status") == "HIT_TOP_1")
        hit_k = sum(1 for log in logs if log.diagnosis.get("status") == "HIT_TOP_K")
        missed = sum(1 for log in logs if log.diagnosis.get("status") == "MISSED")

        hit_1_rate = (hit_1 / total) * 100
        hit_k_rate = ((hit_1 + hit_k) / total) * 100

        print("\n" + "=" * 90)
        print("          🔍 KẾT QUẢ KIỂM THỬ & DEBUG TRUY XUẤT VĂN BẢN (RAG RETRIEVAL)          ")
        print("=" * 90)
        print(f" Tổng số câu hỏi test : {total}")
        print(f" Đúng hoàn hảo (Top 1): {hit_1} ({hit_1_rate:.1f}%)")
        print(f" Đúng trong Top K     : {hit_1 + hit_k} ({hit_k_rate:.1f}%)")
        print(f" Truy xuất thất bại   : {missed} ({(missed/total)*100:.1f}%)")
        print("-" * 90)

        # Header
        print(f"{'ID':<7} | {'Role':<10} | {'Status':<12} | {'Rank':<5} | {'Query (Rút gọn)':<32} | {'Ghi chú'}")
        print("-" * 90)

        for log in logs:
            q_id = log.query_id or "CANARY"
            role = log.user_role
            status = log.diagnosis.get("status", "UNKNOWN")
            rank_str = str(log.diagnosis.get("hit_rank", "-"))
            query_short = (log.input_query[:29] + "...") if len(log.input_query) > 32 else log.input_query
            root_cause = log.diagnosis.get("root_cause") or "OK"

            status_icon = "✅" if status == "HIT_TOP_1" else ("🟡" if status == "HIT_TOP_K" else "🔴")
            print(f"{q_id:<7} | {role:<10} | {status_icon} {status:<9} | {rank_str:<5} | {query_short:<32} | {root_cause}")

        print("=" * 90 + "\n")

    def generate_markdown_report(self) -> str:
        """Generate detailed Markdown report file."""
        now = datetime.now(UTC)
        timestamp_str = now.strftime("%Y%m%d_%H%M%S")
        filepath = self.output_dir / f"debug_report_{timestamp_str}.md"
        json_filepath = self.output_dir / f"debug_logs_{timestamp_str}.json"

        logs = self.logger.logs
        total = len(logs)
        hit_1 = sum(1 for log in logs if log.diagnosis.get("status") == "HIT_TOP_1")
        hit_k = sum(1 for log in logs if log.diagnosis.get("status") == "HIT_TOP_K")
        missed = sum(1 for log in logs if log.diagnosis.get("status") == "MISSED")

        hit_1_rate = (hit_1 / total) * 100 if total else 0
        hit_k_rate = ((hit_1 + hit_k) / total) * 100 if total else 0

        lines = [
            "# Báo cáo Kiểm thử & Debug Truy xuất Văn bản (RAG Retrieval)",
            "",
            f"- **Thời gian chạy**: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"- **Session ID**: `{self.logger.session_id}`",
            f"- **Tổng số test cases**: {total}",
            "",
            "## 1. Tổng quan Tỷ lệ Chính xác",
            "",
            "| Chỉ số | Số lượng | Tỷ lệ (%) | Đánh giá |",
            "| :--- | :--- | :--- | :--- |",
            f"| **Đúng hoàn hảo (Top 1)** | `{hit_1}` / `{total}` | **{hit_1_rate:.1f}%** | {'🟢 Rất tốt' if hit_1_rate >= 80 else '🟡 Cần cải thiện'} |",
            f"| **Đúng trong Top K** | `{hit_1 + hit_k}` / `{total}` | **{hit_k_rate:.1f}%** | {'🟢 Tốt' if hit_k_rate >= 90 else '🟡 Cần kiểm tra'} |",
            f"| **Truy xuất thất bại (Missed)** | `{missed}` / `{total}` | **{(missed/total)*100 if total else 0:.1f}%** | {'🟢 Tuyệt đối' if missed == 0 else '🔴 Cần xử lý'} |",
            "",
            "---",
            "",
            "## 2. Bảng Thống kê Chi tiết từng Câu hỏi",
            "",
            "| Query ID | Role | Câu hỏi | Trạng thái | Hạng | Nguyên nhân & Gợi ý |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        for log in logs:
            q_id = log.query_id or "CANARY"
            status = log.diagnosis.get("status", "UNKNOWN")
            status_badge = "✅ Top 1" if status == "HIT_TOP_1" else ("🟡 Top K" if status == "HIT_TOP_K" else "🔴 Missed")
            rank_str = str(log.diagnosis.get("hit_rank", "-"))
            rec = log.diagnosis.get("recommendation", "")
            lines.append(
                f"| `{q_id}` | `{log.user_role}` | {log.input_query} | {status_badge} | {rank_str} | {rec} |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## 3. Nhật ký Chẩn đoán Chi tiết (Log Breakdown)",
            "",
        ])

        for log in logs:
            q_id = log.query_id or "CANARY"
            status = log.diagnosis.get("status", "UNKNOWN")
            lines.extend([
                f"### Case `{q_id}`: {log.input_query}",
                f"- **Correlation ID**: `{log.correlation_id}`",
                f"- **Vai trò**: `{log.user_role}`",
                f"- **Tài liệu mong đợi**: `{', '.join(log.expected_document_id)}`",
                f"- **Trạng thái**: `{status}` (Hạng: `{log.diagnosis.get('hit_rank', 'N/A')}`)",
                "",
                "#### Top Retrieval Results:",
            ])

            if log.retrieval_results:
                lines.append("| Rank | Score | Title | Document ID | Section |")
                lines.append("| :--- | :--- | :--- | :--- | :--- |")
                for r in log.retrieval_results:
                    lines.append(f"| {r.get('rank', '-')} | `{r.get('score', 0.0):.3f}` | {r.get('title', '')} | `{r.get('document_id', '')}` | {r.get('section', '')} |")
            else:
                lines.append("_Không có tài liệu nào được trả về._")

            if log.final_answer:
                lines.extend([
                    "",
                    "#### LLM Final Answer:",
                    "> " + log.final_answer.replace("\n", "\n> "),
                ])

            lines.extend([
                "",
                f"**Chẩn đoán & Hành động:** {log.diagnosis.get('recommendation', 'N/A')}",
                "",
                "---",
                "",
            ])

        # Save Markdown report
        content = "\n".join(lines)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        # Save JSON log
        self.logger.save_json(str(json_filepath))

        print(f"📄 Báo cáo Markdown đã được lưu tại: {filepath}")
        print(f"📊 Dữ liệu log JSON chi tiết đã lưu tại: {json_filepath}\n")

        return str(filepath)
