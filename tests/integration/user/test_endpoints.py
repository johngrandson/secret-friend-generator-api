"""Integration tests for the /users HTTP endpoints via httpx AsyncClient."""

from uuid import uuid4


async def test_create_user_returns_201(client):
    resp = await client.post("/users/", json={"email": "ep@example.com", "name": "EP User"})

    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "ep@example.com"
    assert body["name"] == "EP User"
    assert body["is_active"] is True
    assert "id" in body


async def test_create_user_duplicate_email_returns_400(client):
    payload = {"email": "dup@example.com", "name": "First"}
    await client.post("/users/", json=payload)

    resp = await client.post("/users/", json={"email": "dup@example.com", "name": "Second"})

    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


async def test_create_user_invalid_email_returns_422(client):
    resp = await client.post("/users/", json={"email": "not-an-email", "name": "X"})

    assert resp.status_code == 422


async def test_list_users_returns_200(client):
    await client.post("/users/", json={"email": "list@example.com", "name": "List User"})

    resp = await client.get("/users/")

    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_get_user_returns_200(client):
    create_resp = await client.post(
        "/users/", json={"email": "get@example.com", "name": "Get User"}
    )
    user_id = create_resp.json()["id"]

    resp = await client.get(f"/users/{user_id}")

    assert resp.status_code == 200
    assert resp.json()["id"] == user_id


async def test_get_nonexistent_user_returns_404(client):
    resp = await client.get(f"/users/{uuid4()}")

    assert resp.status_code == 404


async def test_patch_user_returns_200(client):
    create_resp = await client.post(
        "/users/", json={"email": "patch@example.com", "name": "Before"}
    )
    user_id = create_resp.json()["id"]

    resp = await client.patch(f"/users/{user_id}", json={"name": "After"})

    assert resp.status_code == 200
    assert resp.json()["name"] == "After"


async def test_patch_nonexistent_user_returns_404(client):
    resp = await client.patch(f"/users/{uuid4()}", json={"name": "Ghost"})

    assert resp.status_code == 404


async def test_delete_user_returns_204(client):
    create_resp = await client.post(
        "/users/", json={"email": "del@example.com", "name": "Del User"}
    )
    user_id = create_resp.json()["id"]

    resp = await client.delete(f"/users/{user_id}")

    assert resp.status_code == 204


async def test_delete_nonexistent_user_returns_404(client):
    resp = await client.delete(f"/users/{uuid4()}")

    assert resp.status_code == 404


async def test_delete_then_get_returns_404(client):
    create_resp = await client.post(
        "/users/", json={"email": "gone@example.com", "name": "Gone"}
    )
    user_id = create_resp.json()["id"]

    await client.delete(f"/users/{user_id}")
    resp = await client.get(f"/users/{user_id}")

    assert resp.status_code == 404
