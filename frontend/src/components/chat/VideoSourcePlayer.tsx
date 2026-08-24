/**
 * VideoSourcePlayer — Full video player với chapter markers trên scrubber.
 *
 * Features:
 * - Load video qua Authorization header (Blob URL) để bảo mật
 * - Custom progress bar với marker màu tại mỗi timestamp RAG
 * - Auto-seek đến chunk có rerank_score cao nhất
 * - Hover marker → tooltip: timestamp + section + score + preview
 * - Click "⛶ Toàn màn hình" → modal overlay
 */
import React, { useCallback, useEffect, useRef, useState } from "react";
import { mediaUrl } from "../../services/api";
import type { RetrievedDocInfo } from "../../types";

interface VideoChunk {
  doc: RetrievedDocInfo;
}

interface VideoSourcePlayerProps {
  /** Chunk có rerank_score cao nhất — video này sẽ được load */
  primaryChunk: RetrievedDocInfo;
  /** Tất cả chunks từ cùng video (để vẽ chapter markers) */
  allChunks: RetrievedDocInfo[];
  /** Tổng duration của video (giây) — dùng để tính % position của markers */
  className?: string;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

function ScoreColor(score: number): string {
  if (score >= 5) return "#22c55e";   // xanh lá
  if (score >= 0) return "#3b82f6";   // xanh dương
  if (score >= -3) return "#f97316";  // cam
  return "#ef4444";                   // đỏ
}

interface MarkerTooltipProps {
  chunk: VideoChunk;
  visible: boolean;
  leftPct: number;
}

function MarkerTooltip({ chunk, visible, leftPct }: MarkerTooltipProps) {
  if (!visible) return null;
  const { doc } = chunk;
  return (
    <div
      className="vsp-marker-tooltip"
      style={{ left: `${Math.min(Math.max(leftPct, 5), 85)}%` }}
    >
      <div className="vsp-tooltip-time">
        ⏱ {doc.section || formatTime(doc.timestamp_seconds ?? 0)}
      </div>
      <div className="vsp-tooltip-section">{doc.doc_name}</div>
      {doc.content_preview && (
        <div className="vsp-tooltip-preview">
          "{doc.content_preview.slice(0, 100)}{doc.content_preview.length > 100 ? "…" : ""}"
        </div>
      )}
      <div
        className="vsp-tooltip-score"
        style={{ color: ScoreColor(doc.rerank_score) }}
      >
        Score: {doc.rerank_score.toFixed(1)}
      </div>
    </div>
  );
}

export default function VideoSourcePlayer({
  primaryChunk,
  allChunks,
  className = "",
}: VideoSourcePlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const progressBarRef = useRef<HTMLDivElement>(null);

  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [hoveredMarker, setHoveredMarker] = useState<number | null>(null);

  // ----------------------------------------------------------------
  // Load video qua Authorization header → Blob URL (bảo mật)
  // ----------------------------------------------------------------
  useEffect(() => {
    let objectUrl: string | null = null;
    const controller = new AbortController();

    async function fetchVideo() {
      setLoading(true);
      setError(null);
      try {
        const token = localStorage.getItem("vf_access_token") ?? "";
        const url = mediaUrl(primaryChunk.source_path);
        const response = await fetch(url, {
          signal: controller.signal,
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const blob = await response.blob();
        objectUrl = URL.createObjectURL(blob);
        setBlobUrl(objectUrl);
      } catch (e) {
        if ((e as Error).name !== "AbortError") {
          setError("Không thể tải video. Vui lòng thử lại.");
        }
      } finally {
        setLoading(false);
      }
    }

    fetchVideo();
    return () => {
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [primaryChunk.source_path]);

  // ----------------------------------------------------------------
  // Auto-seek đến chunk có rerank_score cao nhất khi video ready
  // ----------------------------------------------------------------
  const handleLoadedMetadata = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;
    setDuration(video.duration);
    const seekTo = primaryChunk.timestamp_seconds;
    if (seekTo != null && seekTo > 0 && seekTo < video.duration) {
      video.currentTime = seekTo;
    }
  }, [primaryChunk.timestamp_seconds]);

  const handleTimeUpdate = useCallback(() => {
    if (videoRef.current) setCurrentTime(videoRef.current.currentTime);
  }, []);

  const handlePlayPause = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;
    if (isPlaying) {
      video.pause();
    } else {
      video.play();
    }
    setIsPlaying(!isPlaying);
  }, [isPlaying]);

  // ----------------------------------------------------------------
  // Click trên progress bar để seek
  // ----------------------------------------------------------------
  const handleProgressClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const bar = progressBarRef.current;
      const video = videoRef.current;
      if (!bar || !video || duration === 0) return;
      const rect = bar.getBoundingClientRect();
      const pct = (e.clientX - rect.left) / rect.width;
      video.currentTime = pct * duration;
    },
    [duration]
  );

  // ----------------------------------------------------------------
  // Click vào marker → seek đến timestamp đó
  // ----------------------------------------------------------------
  const seekToChunk = useCallback((ts: number) => {
    const video = videoRef.current;
    if (!video) return;
    video.currentTime = ts;
    video.play();
    setIsPlaying(true);
  }, []);

  const progressPct = duration > 0 ? (currentTime / duration) * 100 : 0;

  // ----------------------------------------------------------------
  // Compute marker positions (chỉ chunks có timestamp hợp lệ)
  // ----------------------------------------------------------------
  const markers = allChunks
    .filter((c) => c.timestamp_seconds != null && duration > 0)
    .map((c, i) => ({
      doc: c,
      leftPct: ((c.timestamp_seconds ?? 0) / duration) * 100,
      idx: i,
    }));

  const VideoContent = (
    <div className={`vsp-container ${className}`}>
      {/* Header */}
      <div className="vsp-header">
        <span className="vsp-title">🎬 {primaryChunk.doc_name}</span>
        <button
          className="vsp-fullscreen-btn"
          onClick={() => setIsFullscreen(true)}
          title="Toàn màn hình"
        >
          ⛶ Toàn màn hình
        </button>
      </div>

      {/* Video element */}
      <div className="vsp-video-wrapper">
        {loading && (
          <div className="vsp-loading">
            <div className="vsp-spinner" />
            <span>Đang tải video...</span>
          </div>
        )}
        {error && <div className="vsp-error">{error}</div>}
        {blobUrl && (
          <video
            ref={videoRef}
            className="vsp-video"
            src={blobUrl}
            onLoadedMetadata={handleLoadedMetadata}
            onTimeUpdate={handleTimeUpdate}
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
            onEnded={() => setIsPlaying(false)}
            onClick={handlePlayPause}
            preload="metadata"
          />
        )}
      </div>

      {/* Custom controls */}
      {blobUrl && (
        <div className="vsp-controls">
          <button className="vsp-play-btn" onClick={handlePlayPause}>
            {isPlaying ? "⏸" : "▶"}
          </button>

          {/* Progress bar với chapter markers */}
          <div
            className="vsp-progress-bar"
            ref={progressBarRef}
            onClick={handleProgressClick}
          >
            {/* Filled progress */}
            <div
              className="vsp-progress-fill"
              style={{ width: `${progressPct}%` }}
            />

            {/* Chapter markers */}
            {markers.map((m, i) => (
              <div
                key={i}
                className="vsp-chapter-marker"
                style={{
                  left: `${m.leftPct}%`,
                  background: ScoreColor(m.doc.rerank_score),
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  if (m.doc.timestamp_seconds != null) seekToChunk(m.doc.timestamp_seconds);
                }}
                onMouseEnter={() => setHoveredMarker(i)}
                onMouseLeave={() => setHoveredMarker(null)}
              />
            ))}

            {/* Tooltip cho marker đang hover */}
            {hoveredMarker !== null && markers[hoveredMarker] && (
              <MarkerTooltip
                chunk={markers[hoveredMarker]}
                visible={true}
                leftPct={markers[hoveredMarker].leftPct}
              />
            )}
          </div>

          <span className="vsp-time">
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>
        </div>
      )}
    </div>
  );

  return (
    <>
      {VideoContent}

      {/* Fullscreen Modal */}
      {isFullscreen && (
        <div
          className="vsp-modal-overlay"
          onClick={() => setIsFullscreen(false)}
        >
          <div
            className="vsp-modal-content"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="vsp-modal-close"
              onClick={() => setIsFullscreen(false)}
            >
              ✕
            </button>
            {blobUrl && (
              <video
                className="vsp-modal-video"
                src={blobUrl}
                controls
                autoPlay
                onLoadedMetadata={(e) => {
                  const v = e.currentTarget;
                  const seekTo = primaryChunk.timestamp_seconds;
                  if (seekTo != null && seekTo < v.duration) {
                    v.currentTime = seekTo;
                  }
                }}
              />
            )}
            <div className="vsp-modal-title">{primaryChunk.doc_name}</div>
          </div>
        </div>
      )}
    </>
  );
}
