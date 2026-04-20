"""Tests for ExceptionMiddleware HTTP status code mapping.

Verifies that domain exceptions raised by the service layer are translated
to the correct HTTP responses by ExceptionMiddleware.
"""

from unittest.mock import patch


def test_not_found_error_returns_404_with_detail(client):
    response = client.get("/groups/99999")
    assert response.status_code == 404
    assert response.json()["detail"][0]["msg"] != ""


def test_conflict_error_returns_409_with_detail(client):
    from src.shared.exceptions import ConflictError

    with patch(
        "src.domain.group.service.GroupService.create",
        side_effect=ConflictError("duplicate entry"),
    ):
        response = client.post(
            "/groups", json={"name": "Conflict Group", "description": "d"}
        )
    assert response.status_code == 409
    assert response.json()["detail"][0]["msg"] == "duplicate entry"


def test_business_rule_error_returns_422_with_detail(client):
    group = client.post(
        "/groups", json={"name": "Rule Group", "description": "d"}
    ).json()
    participant = client.post(
        "/participants", json={"name": "Lone Wolf", "group_id": group["id"]}
    ).json()
    # Only one participant — BusinessRuleError is raised by sort_secret_friends
    response = client.post(f"/secret-friends/{group['id']}/{participant['id']}")
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] != ""


def test_unhandled_exception_returns_500(client):
    with patch(
        "src.domain.group.service.GroupService.get_all",
        side_effect=RuntimeError("boom"),
    ):
        response = client.get("/groups")
    assert response.status_code == 500
    assert response.json()["detail"][0]["msg"] == "Unexpected error."
