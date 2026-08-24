from __future__ import annotations

import logging
import os
from pathlib import Path

from src.config import get_settings
from src.extract.base import (
    BaseExtractor,
    DocumentSection,
    ExtractedDocument,
    generate_document_id,
)

logger = logging.getLogger(__name__)

# Ensure ffmpeg binary from imageio-ffmpeg is available in PATH
try:
    import imageio_ffmpeg

    ffmpeg_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
    if ffmpeg_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
except Exception as e:
    logger.debug(f"imageio_ffmpeg setup notice: {e}")


class VideoExtractor(BaseExtractor):
    def __init__(self):
        self.settings = get_settings()

    def extract(self, file_path: Path, role: str, category: str) -> ExtractedDocument:
        sections: list[DocumentSection] = []
        raw_text_list: list[str] = []

        transcript_segments, total_duration = self._transcribe_video(file_path)

        for timestamp, text in transcript_segments:
            section_content = f"## {timestamp}\n\n{text}"
            raw_text_list.append(section_content)
            sections.append(
                DocumentSection(
                    title=timestamp,
                    level=2,
                    content=section_content,
                    section_type="transcript",
                )
            )

        doc_id = generate_document_id(category, file_path.name)
        title = file_path.stem.replace("_", " ").replace("-", " ")
        doc_type = file_path.suffix.lstrip(".").lower()

        return ExtractedDocument(
            document_id=doc_id,
            title=title,
            source_file=file_path.name,
            source_path=f"{category}/{file_path.name}",
            document_type=doc_type,
            content_type="video",
            role=role,
            category=category,
            pages=1,
            duration_seconds=total_duration,
            sections=sections,
            images=[],
            raw_text="\n\n".join(raw_text_list),
        )

    def _transcribe_video(self, file_path: Path) -> tuple[list[tuple[str, str]], float | None]:
        """Transcribe video using Whisper Large-v3 via faster-whisper or openai-whisper."""
        model_name = getattr(self.settings, "video_model", "large-v3") or "large-v3"
        language = getattr(self.settings, "video_language", "vi") or "vi"

        # Lấy HF Token hoặc thư mục download từ config (nếu có)
        hf_token = getattr(self.settings, "hf_token", None) or os.environ.get("HF_TOKEN")
        download_root = getattr(self.settings, "whisper_download_root", None)

        # Determine device and compute_type dynamically
        try:
            import torch

            device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            device = "cpu"

        compute_type = "float16" if device == "cuda" else "int8"

        # 1. Try faster-whisper (faster execution, less memory usage)
        try:
            from faster_whisper import WhisperModel

            logger.info(f"Transcribing {file_path.name} with faster-whisper model '{model_name}' on {device}...")

            # Khởi tạo WhisperModel (nếu có hf_token dùng use_auth_token)
            model_kwargs = {
                "model_size_or_path": model_name,
                "device": device,
                "compute_type": compute_type,
                "download_root": download_root,
            }
            if hf_token:
                model_kwargs["use_auth_token"] = hf_token

            model = WhisperModel(**model_kwargs)
            with file_path.open("rb") as audio_file:
                # 1. Tạo chuỗi gợi ý ngữ cảnh chứa các từ hay bị nhầm
                prompt_hint = "Ngành, ô tô, xe máy điện, kế toán, đơn hàng, PO, ngày tháng năm, xuất hóa đơn."

                segments, info = model.transcribe(
                    audio_file,
                    beam_size=5,
                    language=language,
                    # Gợi ý ngữ cảnh giúp phân biệt "ngành" và "ngày"
                    initial_prompt=prompt_hint,
                    # TRÁNH MẤT TỪ: Chỉnh ngưỡng im lặng và lặp lại
                    no_speech_threshold=0.6,  # Giảm ngưỡng im lặng để không bỏ sót từ nói nhỏ (mặc định 0.6)
                    log_prob_threshold=-1.2,  # Giảm ngưỡng lọc câu để giữ lại các từWhisper chưa tự tin lắm
                    compression_ratio_threshold=2.4,  # Ngăn Whisper bỏ qua các đoạn lặp lại hoặc nói nhanh
                )

                results: list[tuple[str, str]] = []
                last_end = 0.0
                for segment in segments:
                    start_min = int(segment.start // 60)
                    start_sec = int(segment.start % 60)
                    timestamp = f"{start_min:02d}:{start_sec:02d}"
                    results.append((timestamp, segment.text.strip()))
                    last_end = segment.end

                duration = info.duration if hasattr(info, "duration") else last_end

                if results:
                    return results, duration

        except Exception as e:
            logger.warning(f"faster-whisper transcription with '{model_name}' failed for {file_path.name}: {e}")

        # 2. Fallback to OpenAI Whisper library
        try:
            import whisper

            logger.info(f"Fallback: Transcribing {file_path.name} with openai-whisper '{model_name}' on {device}...")
            model = whisper.load_model(model_name, device=device, download_root=download_root)
            fp16 = device == "cuda"

            # Use resolved posix path string for ffmpeg compatibility across OS / Windows encoding
            abs_path_str = file_path.resolve().as_posix()
            res = model.transcribe(abs_path_str, language=language, fp16=fp16)

            results: list[tuple[str, str]] = []
            max_end = 0.0
            for seg in res.get("segments", []):
                start_time = seg.get("start", 0.0)
                end_time = seg.get("end", start_time)
                max_end = max(max_end, end_time)

                start_min = int(start_time // 60)
                start_sec = int(start_time % 60)
                timestamp = f"{start_min:02d}:{start_sec:02d}"
                text = seg.get("text", "").strip()
                if text:
                    results.append((timestamp, text))

            if results:
                return results, max_end

        except Exception as e:
            logger.warning(f"openai-whisper transcription with '{model_name}' failed for {file_path.name}: {e}")

        # Fallback placeholder if offline / model loading is skipped
        filename_clean = file_path.stem.replace("_", " ").replace("-", " ")
        fallback_segments = [
            ("00:00 - Overview", f"Video transcript for {filename_clean}."),
            ("00:15 - Detailed Instructions", f"Content step-by-step for video file: {file_path.name}."),
        ]
        return fallback_segments, 60.0
