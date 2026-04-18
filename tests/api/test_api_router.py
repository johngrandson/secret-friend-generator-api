def test_healthcheck_returns_200(client):
    response = client.get("/healthcheck")
    assert response.status_code == 200


def test_healthcheck_returns_ok_status(client):
    response = client.get("/healthcheck")
    assert response.json() == {"status": "ok"}
