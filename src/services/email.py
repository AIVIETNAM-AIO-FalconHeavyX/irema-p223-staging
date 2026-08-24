"""Transactional email delivery for account invitations."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from urllib.parse import quote

from src.config import get_settings


def send_invitation_email(*, recipient: str, token: str, role: str) -> None:
    settings = get_settings()
    if not settings.resend_api_key or not settings.email_from:
        raise RuntimeError("Invitation email is not configured")

    link = f"{settings.frontend_url.rstrip('/')}/invite/accept?token={quote(token)}"
    payload = json.dumps(
        {
            "from": settings.email_from,
            "to": [recipient],
            "subject": "You are invited to VF AI Onboarding",
            "html": (
                f"<p>You have been invited as <strong>{role}</strong>.</p>"
                f'<p><a href="{link}">Accept invitation and create your password</a></p>'
                f"<p>This link expires in {settings.invite_ttl_hours} hours.</p>"
            ),
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={"Authorization": f"Bearer {settings.resend_api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            if response.status >= 300:
                raise RuntimeError("Email provider rejected invitation")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError("Email provider unavailable") from exc
