import pytest

from src.db.models import UserRole


@pytest.mark.asyncio
async def test_public_registration_requires_invitation(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "public-sale@example.com",
            "password": "password123",
            "full_name": "Public User",
            "role": "sale",
        },
    )
    assert response.status_code == 403
    assert "invitation" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_owner_cannot_invite_privileged_roles(client, monkeypatch):
    monkeypatch.setattr("src.api.auth_routes.send_invitation_email", lambda **_kwargs: None)
    login = await client.post("/api/v1/auth/login", json={"email": "thehung@vinfast.vn", "password": "12345678"})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    for role in (UserRole.owner.value, UserRole.vinfast.value):
        response = await client.post(
            "/api/v1/auth/invite",
            headers=headers,
            json={"email": f"{role}@example.com", "role": role},
        )
        assert response.status_code == 422
