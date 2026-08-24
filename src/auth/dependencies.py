"""FastAPI dependency to extract and validate the current user from JWT."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.auth.security import decode_token
from src.db import get_db
from src.db.crud import get_user_by_id
from src.db.models import User

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Dependency: parse Bearer JWT and return the authenticated User."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chưa đăng nhập. Vui lòng cung cấp token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token thiếu thông tin.")

    user = get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Tài khoản không tồn tại hoặc bị vô hiệu hóa."
        )

    return user


def get_current_user_allow_query_token(
    token: str | None = Query(default=None, description="JWT thay cho header Authorization"),
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Như get_current_user nhưng chấp nhận thêm JWT truyền qua query `?token=`.

    Thẻ <video src> và <iframe src> của trình duyệt không gửi được header
    Authorization, nên endpoint phục vụ file phải nhận token qua query string.
    """
    raw_token = credentials.credentials if credentials else token
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chưa đăng nhập. Vui lòng cung cấp token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(raw_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_id(db, payload.get("sub") or "")
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản không tồn tại hoặc bị vô hiệu hóa.",
        )
    return user


def require_owner(current_user: User = Depends(get_current_user)) -> User:
    """Dependency: requires the user to have the 'owner' role."""
    if current_user.role.value != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Owner đại lý mới có quyền thực hiện thao tác này.",
        )
    return current_user


def require_manager_or_owner(current_user: User = Depends(get_current_user)) -> User:
    """Dependency: requires the user to have the 'manager' or 'owner' role."""
    if current_user.role.value not in ("manager", "owner"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Manager hoặc Owner mới có quyền thực hiện thao tác này.",
        )
    return current_user


def require_vinfast(current_user: User = Depends(get_current_user)) -> User:
    """Dependency: requires the user to have the 'vinfast' role."""
    if current_user.role.value != "vinfast":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ VinFast mới có quyền thực hiện thao tác này.",
        )
    return current_user


def require_vinfast_or_owner(current_user: User = Depends(get_current_user)) -> User:
    """Dependency: requires the user to have the 'vinfast' or 'owner' role."""
    if current_user.role.value not in ("vinfast", "owner"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ VinFast hoặc Owner mới có quyền thực hiện thao tác này.",
        )
    return current_user
