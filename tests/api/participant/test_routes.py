def _create_group(client, name: str = "Test Group") -> dict:
    return client.post("/groups", json={"name": name, "description": "desc"}).json()


def _create_participant(client, group_id: int, name: str = "Alice") -> dict:
    return client.post(
        "/participants", json={"name": name, "group_id": group_id}
    ).json()


def test_create_participant_returns_201(client):
    group = _create_group(client, "Part Group")
    response = client.post(
        "/participants", json={"name": "Alice", "group_id": group["id"]}
    )
    assert response.status_code == 201


def test_create_participant_response_contains_id_and_name(client):
    group = _create_group(client, "Name Group")
    response = client.post(
        "/participants", json={"name": "Bob", "group_id": group["id"]}
    )
    data = response.json()
    assert "id" in data
    assert data["name"] == "Bob"


def test_create_participant_with_invalid_group_returns_404(client):
    response = client.post("/participants", json={"name": "Ghost", "group_id": 99999})
    assert response.status_code == 404


def test_create_participant_missing_name_returns_422(client):
    group = _create_group(client, "Miss Group")
    response = client.post("/participants", json={"group_id": group["id"]})
    assert response.status_code == 422


def test_list_participants_returns_200(client):
    response = client.get("/participants")
    assert response.status_code == 200


def test_list_participants_response_contains_participants_key(client):
    response = client.get("/participants")
    assert "participants" in response.json()


def test_list_participants_includes_created_participant(client):
    group = _create_group(client, "List Group")
    _create_participant(client, group["id"], "Listed Person")
    response = client.get("/participants")
    names = [p["name"] for p in response.json()["participants"]]
    assert "Listed Person" in names


def test_get_participant_by_id_returns_200(client):
    group = _create_group(client, "Fetch Group")
    participant = _create_participant(client, group["id"], "Fetched")
    response = client.get(f"/participants/{participant['id']}")
    assert response.status_code == 200


def test_get_participant_by_id_returns_correct_participant(client):
    group = _create_group(client, "ID Group")
    participant = _create_participant(client, group["id"], "Correct")
    response = client.get(f"/participants/{participant['id']}")
    assert response.json()["id"] == participant["id"]


def test_get_participant_by_id_nonexistent_returns_404(client):
    response = client.get("/participants/99999")
    assert response.status_code == 404


def test_update_participant_returns_200(client):
    group = _create_group(client, "Update Group")
    participant = _create_participant(client, group["id"], "Old Name")
    response = client.patch(
        f"/participants/{participant['id']}",
        json={"name": "New Name"},
    )
    assert response.status_code == 200


def test_update_participant_name_reflects_in_response(client):
    group = _create_group(client, "Rename Group")
    participant = _create_participant(client, group["id"], "Before")
    response = client.patch(
        f"/participants/{participant['id']}",
        json={"name": "After"},
    )
    assert response.json()["name"] == "After"


def test_update_participant_nonexistent_returns_404(client):
    response = client.patch("/participants/99999", json={"name": "Nobody"})
    assert response.status_code == 404


def test_update_participant_empty_body_returns_422(client):
    group = _create_group(client, "Empty Update Group")
    participant = _create_participant(client, group["id"], "Someone")
    response = client.patch(f"/participants/{participant['id']}", json={})
    assert response.status_code == 422


def test_delete_participant_returns_204(client):
    group = _create_group(client, "Delete Group")
    participant = _create_participant(client, group["id"], "ToBeDeleted")
    response = client.delete(f"/participants/{participant['id']}")
    assert response.status_code == 204


def test_delete_participant_nonexistent_returns_404(client):
    response = client.delete("/participants/99999")
    assert response.status_code == 404


def test_delete_participant_verify_not_found_after_delete(client):
    group = _create_group(client, "Verify Delete Group")
    participant = _create_participant(client, group["id"], "ToVerify")
    client.delete(f"/participants/{participant['id']}")
    response = client.get(f"/participants/{participant['id']}")
    assert response.status_code == 404
