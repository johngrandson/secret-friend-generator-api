def test_create_group_returns_201(client):
    response = client.post(
        "/groups",
        json={"name": "Book Club", "description": "Monthly reads"},
    )
    assert response.status_code == 201


def test_create_group_response_contains_id_and_name(client):
    response = client.post(
        "/groups",
        json={"name": "Wine Night", "description": "desc"},
    )
    data = response.json()
    assert "id" in data
    assert data["name"] == "Wine Night"


def test_create_group_response_contains_link_url(client):
    response = client.post(
        "/groups",
        json={"name": "Token Test", "description": "desc"},
    )
    data = response.json()
    assert data["link_url"] is not None


def test_create_group_name_too_short_returns_422(client):
    response = client.post(
        "/groups",
        json={"name": "AB", "description": "desc"},
    )
    assert response.status_code == 422


def test_create_group_missing_name_returns_422(client):
    response = client.post("/groups", json={"description": "desc"})
    assert response.status_code == 422


def test_list_groups_returns_200(client):
    response = client.get("/groups")
    assert response.status_code == 200


def test_list_groups_response_contains_groups_key(client):
    response = client.get("/groups")
    assert "groups" in response.json()


def test_list_groups_includes_created_group(client):
    client.post("/groups", json={"name": "Listed Group", "description": "d"})
    response = client.get("/groups")
    names = [g["name"] for g in response.json()["groups"]]
    assert "Listed Group" in names


def test_get_group_by_id_returns_200(client):
    created = client.post(
        "/groups", json={"name": "Fetch Group", "description": "d"}
    ).json()
    response = client.get(f"/groups/{created['id']}")
    assert response.status_code == 200


def test_get_group_by_id_returns_correct_group(client):
    created = client.post(
        "/groups", json={"name": "Correct Group", "description": "d"}
    ).json()
    response = client.get(f"/groups/{created['id']}")
    assert response.json()["id"] == created["id"]


def test_get_group_by_id_nonexistent_returns_404(client):
    response = client.get("/groups/99999")
    assert response.status_code == 404


def test_get_group_by_link_url_returns_200(client):
    created = client.post(
        "/groups", json={"name": "Link Group", "description": "d"}
    ).json()
    link_url = created["link_url"]
    response = client.get(f"/groups/link/{link_url}")
    assert response.status_code == 200


def test_get_group_by_link_url_returns_correct_group(client):
    created = client.post(
        "/groups", json={"name": "URL Match Group", "description": "d"}
    ).json()
    link_url = created["link_url"]
    response = client.get(f"/groups/link/{link_url}")
    assert response.json()["id"] == created["id"]


def test_get_group_by_link_url_nonexistent_returns_404(client):
    response = client.get("/groups/link/no-such-token")
    assert response.status_code == 404
