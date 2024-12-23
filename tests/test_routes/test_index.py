def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok", "message": "Welcome to the SMSE API"}
