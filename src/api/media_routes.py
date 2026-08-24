"""Phục vụ tài liệu onboarding (video/PDF/Office) từ data/raw.

Không mount StaticFiles vì cần 3 thứ StaticFiles không làm được:
  1. Bắt buộc JWT — dữ liệu đại lý không được để public.
  2. RBAC — mỗi vai trò chỉ tải được đúng tài liệu trong lộ trình của mình.
  3. Chặn path traversal trên đường dẫn do client gửi lên.
Việc stream + hỗ trợ Range (tua video) do FileResponse của Starlette đảm nhiệm.
"""

from __future__ import annotations

from email.utils import formatdate
from pathlib import Path
import unicodedata
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from src.auth.dependencies import get_current_user_allow_query_token
from src.content.onboarding_catalog import resource_modules_for_role, resource_paths_for_role
from src.db import get_db
from src.db.crud import get_module_statuses, seed_onboarding_steps
from src.db.models import User
from src.media import (
    guess_media_type,
    normalize_path,
    resolve_media_path,
)

router = APIRouter()


@router.get("/files/{file_path:path}")
def get_onboarding_file(
    file_path: str,
    request: Request,
    download: bool = Query(default=False, description="Trả về dạng tải xuống thay vì xem trực tiếp"),
    current_user: User = Depends(get_current_user_allow_query_token),
    db: Session = Depends(get_db),
):
    """Trả về một tài liệu trong lộ trình onboarding của user hiện tại."""
    relative = normalize_path(file_path)

    # RBAC: chỉ cho phép đúng những file nằm trong lộ trình của vai trò này.
    if relative not in resource_paths_for_role(current_user.role.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài liệu này không thuộc lộ trình hội nhập của bạn.",
        )

    seed_onboarding_steps(db)
    allowed_modules = resource_modules_for_role(current_user.role.value, relative)
    unlocked_modules = {item["module_id"] for item in get_module_statuses(db, current_user) if item["unlocked"]}
    if allowed_modules and not allowed_modules.intersection(unlocked_modules):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Module chứa tài liệu này chưa được mở.",
        )

    try:
        path = resolve_media_path(relative)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Đường dẫn không hợp lệ.")

    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài liệu.")

    stat_result = path.stat()
    mtime = int(stat_result.st_mtime)
    size = stat_result.st_size
    etag = f'"{mtime}-{size}"'
    last_modified = formatdate(stat_result.st_mtime, usegmt=True)

    # Revalidation: nếu client có ETag khớp thì trả 304 Not Modified
    if_none_match = request.headers.get("if-none-match")
    if if_none_match and if_none_match.strip() == etag:
        return Response(
            status_code=status.HTTP_304_NOT_MODIFIED,
            headers={
                "ETag": etag,
                "Last-Modified": last_modified,
                "Cache-Control": "private, no-cache",
            },
        )

    if download:
        encoded_name = quote(path.name)
        disposition = f"attachment; filename*=UTF-8''{encoded_name}"
    else:
        disposition = "inline"

    return FileResponse(
        path,
        media_type=guess_media_type(path),
        headers={
            "Content-Disposition": disposition,
            "Cache-Control": "private, no-cache",
            "ETag": etag,
            "Last-Modified": last_modified,
        },
    )


@router.get("/s3-files/{object_key:path}")
def stream_minio_file(
    object_key: str,
    download: bool = Query(default=False, description="Tải xuống thay vì xem trực tiếp"),
    current_user: User = Depends(get_current_user_allow_query_token),
):
    """Proxy stream file trực tiếp từ MinIO qua backend để các client ngrok/remote xem được."""
    from botocore.exceptions import ClientError
    from src.cloud.s3_service import s3_service

    clean_key = object_key.lstrip("/")
    candidates = [
        clean_key,
        unicodedata.normalize("NFC", clean_key),
        unicodedata.normalize("NFD", clean_key),
    ]

    s3_obj = None
    for candidate in dict.fromkeys(candidates):
        try:
            s3_obj = s3_service.s3_client.get_object(
                Bucket=s3_service.bucket_name,
                Key=candidate,
            )
            break
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "NoSuchKey":
                continue
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi S3: {e}")
        except Exception:
            continue

    file_name = clean_key.split("/")[-1]

    # Fallback: thử tìm file trong thư mục local data/raw
    try:
        fallback_path = resolve_media_path(file_name)
    except ValueError:
        fallback_path = Path(file_name)

    if not s3_obj:
        if fallback_path.is_file():
            return FileResponse(
                fallback_path,
                media_type=guess_media_type(fallback_path),
                headers={
                    "Content-Disposition": f"{'attachment' if download else 'inline'}; filename*=UTF-8''{quote(fallback_path.name)}",
                    "Cache-Control": "private, max-age=3600",
                },
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File '{file_name}' không tồn tại trên MinIO hoặc thư mục lưu trữ.")

    content_type = guess_media_type(Path(file_name))
    if content_type == "application/octet-stream" and "ContentType" in s3_obj:
        content_type = s3_obj["ContentType"]

    encoded_name = quote(file_name)
    disposition = "attachment" if download else "inline"

    headers = {
        "Content-Disposition": f"{disposition}; filename*=UTF-8''{encoded_name}",
        "Cache-Control": "private, max-age=3600",
    }
    if "ContentLength" in s3_obj:
        headers["Content-Length"] = str(s3_obj["ContentLength"])

    return StreamingResponse(
        s3_obj["Body"],
        media_type=content_type,
        headers=headers,
    )
