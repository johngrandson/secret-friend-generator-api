def _create_group(client, name: str = "SF Group") -> dict:
    return client.post("/groups", json={"name": name, "description": "desc"}).json()


def _create_participant(client, group_id: int, name: str = "Person") -> dict:
    return client.post(
        "/participants", json={"name": name, "group_id": group_id}
    ).json()


def test_generate_secret_friends_returns_200(client):
    group = _create_group(client, "Reveal Group")
    p1 = _create_participant(client, group["id"], "Giver")
    _create_participant(client, group["id"], "Receiver")

    response = client.post(f"/secret-friends/{group['id']}/{p1['id']}")
    assert response.status_code == 200


def test_generate_secret_friends_response_contains_secret_friends_key(client):
    group = _create_group(client, "Key Group")
    p1 = _create_participant(client, group["id"], "Person A")
    _create_participant(client, group["id"], "Person B")

    response = client.post(f"/secret-friends/{group['id']}/{p1['id']}")
    assert "secret_friends" in response.json()


def test_generate_secret_friends_receiver_differs_from_giver(client):
    group = _create_group(client, "Distinct Group")
    p1 = _create_participant(client, group["id"], "Giver X")
    _create_participant(client, group["id"], "Receiver X")

    response = client.post(f"/secret-friends/{group['id']}/{p1['id']}")
    sf = response.json()["secret_friends"]
    assert sf["gift_giver_id"] != sf["gift_receiver_id"]


def test_generate_secret_friends_nonexistent_participant_returns_404(client):
    group = _create_group(client, "Missing Part Group")
    response = client.post(f"/secret-friends/{group['id']}/99999")
    assert response.status_code == 404


def test_generate_secret_friends_with_only_one_participant_returns_400(client):
    group = _create_group(client, "Solo Group")
    p1 = _create_participant(client, group["id"], "Lonely")

    response = client.post(f"/secret-friends/{group['id']}/{p1['id']}")
    assert response.status_code == 422


def test_generate_secret_friends_giver_id_matches_participant_id(client):
    group = _create_group(client, "Giver ID Group")
    p1 = _create_participant(client, group["id"], "The Giver")
    _create_participant(client, group["id"], "The Receiver")

    response = client.post(f"/secret-friends/{group['id']}/{p1['id']}")
    sf = response.json()["secret_friends"]
    assert sf["gift_giver_id"] == p1["id"]


def _create_secret_friend(client) -> dict:
    group = _create_group(client, "Get/Del Group")
    p1 = _create_participant(client, group["id"], "Alpha")
    _create_participant(client, group["id"], "Beta")
    response = client.post(f"/secret-friends/{group['id']}/{p1['id']}")
    return response.json()["secret_friends"]


def test_get_secret_friend_returns_200(client):
    sf = _create_secret_friend(client)
    response = client.get(f"/secret-friends/{sf['id']}")
    assert response.status_code == 200


def test_get_secret_friend_nonexistent_returns_404(client):
    response = client.get("/secret-friends/99999")
    assert response.status_code == 404


def test_delete_secret_friend_returns_204(client):
    sf = _create_secret_friend(client)
    response = client.delete(f"/secret-friends/{sf['id']}")
    assert response.status_code == 204


def test_delete_secret_friend_nonexistent_returns_404(client):
    response = client.delete("/secret-friends/99999")
    assert response.status_code == 404


def test_delete_secret_friend_verify_not_found_after_delete(client):
    sf = _create_secret_friend(client)
    client.delete(f"/secret-friends/{sf['id']}")
    response = client.get(f"/secret-friends/{sf['id']}")
    assert response.status_code == 404


def test_get_secret_friend_returns_correct_fields(client):
    sf = _create_secret_friend(client)
    response = client.get(f"/secret-friends/{sf['id']}")
    data = response.json()
    assert "id" in data
    assert "gift_giver_id" in data
    assert "gift_receiver_id" in data
