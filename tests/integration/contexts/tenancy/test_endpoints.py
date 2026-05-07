"""Integration tests for the /organizations HTTP endpoints."""

from uuid import uuid4


async def test_create_organization_returns_201(client):
    owner = str(uuid4())
    resp = await client.post(
        "/organizations/",
        json={"name": "Acme", "slug": "acme", "owner_user_id": owner},
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Acme"
    assert body["slug"] == "acme"
    assert len(body["members"]) == 1
    assert body["members"][0]["user_id"] == owner
    assert body["members"][0]["role"] == "OWNER"


async def test_create_duplicate_slug_returns_400(client):
    payload = {
        "name": "Acme",
        "slug": "dup-slug",
        "owner_user_id": str(uuid4()),
    }
    await client.post("/organizations/", json=payload)

    resp = await client.post(
        "/organizations/",
        json={"name": "Other", "slug": "dup-slug", "owner_user_id": str(uuid4())},
    )

    assert resp.status_code == 400
    assert "already taken" in resp.json()["detail"].lower()


async def test_create_invalid_slug_returns_400(client):
    resp = await client.post(
        "/organizations/",
        json={
            "name": "Acme",
            "slug": "Invalid Slug!",
            "owner_user_id": str(uuid4()),
        },
    )

    assert resp.status_code == 400


async def test_add_member_returns_201(client):
    owner = str(uuid4())
    create_resp = await client.post(
        "/organizations/",
        json={"name": "Beta", "slug": "beta", "owner_user_id": owner},
    )
    org_id = create_resp.json()["id"]
    new_user = str(uuid4())

    resp = await client.post(
        f"/organizations/{org_id}/members",
        json={"user_id": new_user, "role": "MEMBER"},
    )

    assert resp.status_code == 201
    body = resp.json()
    assert any(m["user_id"] == new_user for m in body["members"])


async def test_add_member_to_nonexistent_org_returns_404(client):
    resp = await client.post(
        f"/organizations/{uuid4()}/members",
        json={"user_id": str(uuid4()), "role": "MEMBER"},
    )

    assert resp.status_code == 404


async def test_add_duplicate_member_returns_400(client):
    owner = str(uuid4())
    create_resp = await client.post(
        "/organizations/",
        json={"name": "Gamma", "slug": "gamma", "owner_user_id": owner},
    )
    org_id = create_resp.json()["id"]

    resp = await client.post(
        f"/organizations/{org_id}/members",
        json={"user_id": owner, "role": "ADMIN"},
    )

    assert resp.status_code == 400


async def test_remove_member_returns_200(client):
    owner = str(uuid4())
    member = str(uuid4())
    create_resp = await client.post(
        "/organizations/",
        json={"name": "Delta", "slug": "delta", "owner_user_id": owner},
    )
    org_id = create_resp.json()["id"]
    await client.post(
        f"/organizations/{org_id}/members",
        json={"user_id": member, "role": "MEMBER"},
    )

    resp = await client.delete(f"/organizations/{org_id}/members/{member}")

    assert resp.status_code == 200
    body = resp.json()
    assert all(m["user_id"] != member for m in body["members"])


async def test_remove_last_owner_returns_400(client):
    owner = str(uuid4())
    create_resp = await client.post(
        "/organizations/",
        json={"name": "Epsilon", "slug": "epsilon", "owner_user_id": owner},
    )
    org_id = create_resp.json()["id"]

    resp = await client.delete(f"/organizations/{org_id}/members/{owner}")

    assert resp.status_code == 400
    assert "last OWNER" in resp.json()["detail"]


async def test_change_member_role_returns_200(client):
    owner = str(uuid4())
    member = str(uuid4())
    create_resp = await client.post(
        "/organizations/",
        json={"name": "Zeta", "slug": "zeta", "owner_user_id": owner},
    )
    org_id = create_resp.json()["id"]
    await client.post(
        f"/organizations/{org_id}/members",
        json={"user_id": member, "role": "MEMBER"},
    )

    resp = await client.patch(
        f"/organizations/{org_id}/members/{member}", json={"role": "ADMIN"}
    )

    assert resp.status_code == 200
    body = resp.json()
    target = next(m for m in body["members"] if m["user_id"] == member)
    assert target["role"] == "ADMIN"


async def test_demote_last_owner_returns_400(client):
    owner = str(uuid4())
    create_resp = await client.post(
        "/organizations/",
        json={"name": "Eta", "slug": "eta", "owner_user_id": owner},
    )
    org_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/organizations/{org_id}/members/{owner}", json={"role": "MEMBER"}
    )

    assert resp.status_code == 400
    assert "last OWNER" in resp.json()["detail"]


async def test_list_my_organizations_returns_user_orgs(client):
    user = str(uuid4())
    other = str(uuid4())
    await client.post(
        "/organizations/",
        json={"name": "Mine A", "slug": "mine-a", "owner_user_id": user},
    )
    await client.post(
        "/organizations/",
        json={"name": "Mine B", "slug": "mine-b", "owner_user_id": user},
    )
    await client.post(
        "/organizations/",
        json={"name": "Other", "slug": "other-org", "owner_user_id": other},
    )

    resp = await client.get(f"/organizations/?user_id={user}")

    assert resp.status_code == 200
    body = resp.json()
    slugs = {o["slug"] for o in body["organizations"]}
    assert slugs == {"mine-a", "mine-b"}


async def test_list_my_organizations_returns_empty_for_unknown_user(client):
    resp = await client.get(f"/organizations/?user_id={uuid4()}")

    assert resp.status_code == 200
    assert resp.json()["organizations"] == []
