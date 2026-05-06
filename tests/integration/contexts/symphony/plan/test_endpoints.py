"""Integration tests for the /plans HTTP endpoints via httpx AsyncClient."""

from uuid import uuid4


async def _create_run(client) -> str:
    resp = await client.post("/runs/", json={"issue_id": "ENG-plan"})
    assert resp.status_code == 201
    return str(resp.json()["id"])


async def test_create_plan_returns_201(client):
    run_id = await _create_run(client)

    resp = await client.post(
        "/plans/",
        json={"run_id": run_id, "version": 1, "content": "plan content"},
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["run_id"] == run_id
    assert body["version"] == 1
    assert body["content"] == "plan content"
    assert "id" in body


async def test_create_plan_missing_field_returns_422(client):
    resp = await client.post("/plans/", json={"version": 1, "content": "x"})

    assert resp.status_code == 422


async def test_get_plan_returns_200(client):
    run_id = await _create_run(client)
    create_resp = await client.post(
        "/plans/",
        json={"run_id": run_id, "version": 1, "content": "get me"},
    )
    plan_id = str(create_resp.json()["id"])

    resp = await client.get(f"/plans/{plan_id}")

    assert resp.status_code == 200
    assert resp.json()["id"] == plan_id


async def test_get_nonexistent_plan_returns_404(client):
    resp = await client.get(f"/plans/{uuid4()}")

    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


async def test_list_plans_for_run_returns_200_with_list(client):
    run_id = await _create_run(client)
    await client.post(
        "/plans/",
        json={"run_id": run_id, "version": 1, "content": "v1"},
    )

    resp = await client.get(f"/plans/?run_id={run_id}")

    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) == 1


async def test_approve_plan_returns_200(client):
    run_id = await _create_run(client)
    create_resp = await client.post(
        "/plans/",
        json={"run_id": run_id, "version": 1, "content": "approve me"},
    )
    plan_id = str(create_resp.json()["id"])

    resp = await client.post(
        f"/plans/{plan_id}/approve", json={"approved_by": "alice"}
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["approved_by"] == "alice"
    assert body["approved_at"] is not None


async def test_approve_plan_twice_returns_400(client):
    run_id = await _create_run(client)
    create_resp = await client.post(
        "/plans/",
        json={"run_id": run_id, "version": 1, "content": "write-once"},
    )
    plan_id = str(create_resp.json()["id"])

    await client.post(f"/plans/{plan_id}/approve", json={"approved_by": "alice"})
    resp = await client.post(
        f"/plans/{plan_id}/approve", json={"approved_by": "bob"}
    )

    assert resp.status_code == 400


async def test_approve_nonexistent_plan_returns_404(client):
    resp = await client.post(
        f"/plans/{uuid4()}/approve", json={"approved_by": "alice"}
    )

    assert resp.status_code == 404


async def test_reject_plan_returns_200(client):
    run_id = await _create_run(client)
    create_resp = await client.post(
        "/plans/",
        json={"run_id": run_id, "version": 1, "content": "reject me"},
    )
    plan_id = str(create_resp.json()["id"])

    resp = await client.post(
        f"/plans/{plan_id}/reject", json={"reason": "too vague"}
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["rejection_reason"] == "too vague"


async def test_reject_nonexistent_plan_returns_404(client):
    resp = await client.post(
        f"/plans/{uuid4()}/reject", json={"reason": "gone"}
    )

    assert resp.status_code == 404


async def test_create_plan_returns_400_when_version_is_zero(client):
    run_id = await _create_run(client)

    resp = await client.post(
        "/plans/",
        json={"run_id": run_id, "version": 0, "content": "x"},
    )

    assert resp.status_code == 400
    assert "version" in resp.json()["detail"].lower()


async def test_reject_plan_returns_400_when_already_approved(client):
    run_id = await _create_run(client)
    create_resp = await client.post(
        "/plans/",
        json={"run_id": run_id, "version": 1, "content": "write-once"},
    )
    plan_id = str(create_resp.json()["id"])

    await client.post(f"/plans/{plan_id}/approve", json={"approved_by": "ops"})
    resp = await client.post(f"/plans/{plan_id}/reject", json={"reason": "x"})

    assert resp.status_code == 400
    assert "not found" not in resp.json()["detail"].lower()
