"""Integration tests for the /runs HTTP endpoints via httpx AsyncClient."""

from uuid import uuid4


async def test_create_run_returns_201(client):
    resp = await client.post("/runs/", json={"issue_id": "ENG-1"})

    assert resp.status_code == 201
    body = resp.json()
    assert body["issue_id"] == "ENG-1"
    assert body["status"] == "received"
    assert "id" in body


async def test_create_run_missing_field_returns_422(client):
    resp = await client.post("/runs/", json={})

    assert resp.status_code == 422


async def test_list_runs_returns_200_with_list(client):
    await client.post("/runs/", json={"issue_id": "ENG-2"})

    resp = await client.get("/runs/")

    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_get_run_returns_200(client):
    create_resp = await client.post("/runs/", json={"issue_id": "ENG-3"})
    run_id = create_resp.json()["id"]

    resp = await client.get(f"/runs/{run_id}")

    assert resp.status_code == 200
    assert resp.json()["id"] == run_id


async def test_get_nonexistent_run_returns_404(client):
    resp = await client.get(f"/runs/{uuid4()}")

    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


async def test_list_runs_returns_created_run(client):
    create_resp = await client.post("/runs/", json={"issue_id": "ENG-4"})
    run_id = create_resp.json()["id"]

    resp = await client.get("/runs/")

    ids = [r["id"] for r in resp.json()]
    assert run_id in ids


async def test_create_run_returns_400_when_issue_id_blank(client):
    resp = await client.post("/runs/", json={"issue_id": "  "})

    assert resp.status_code == 400
    assert "blank" in resp.json()["detail"].lower()
