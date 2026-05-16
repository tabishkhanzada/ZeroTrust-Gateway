import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "securepassword123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    # First register
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "password": "password123"}
    )

    # Then login
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_protected_route_access(client: AsyncClient):
    email = "protected@example.com"
    password = "password123"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password}
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    token = login_res.json()["access_token"]

    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == email

@pytest.mark.asyncio
async def test_logout_blacklist(client: AsyncClient):
    email = "logout@example.com"
    password = "password123"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password}
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    token = login_res.json()["access_token"]

    # Logout
    logout_res = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert logout_res.status_code == 200

    # Try to access protected route again with same token
    retry_res = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert retry_res.status_code == 401
    assert retry_res.json()["detail"] == "Token has been revoked"

@pytest.mark.asyncio
async def test_refresh_token_rotation(client: AsyncClient):
    email = "refresh@example.com"
    password = "password123"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password}
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    refresh_token = login_res.json()["refresh_token"]

    # Rotate tokens
    response = await client.post(
        "/api/v1/auth/refresh",
        params={"refresh_token_in": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
