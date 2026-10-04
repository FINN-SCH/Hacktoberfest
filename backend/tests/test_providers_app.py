from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app

def test_health_and_api_404_without_provider_initialization(tmp_path):
    (tmp_path / "index.html").write_text("<html>Test SPA</html>")
    (tmp_path / "asset.js").write_text("export default 1")
    app = create_app(Settings(_env_file=None,db_path=tmp_path / "test.db"), frontend_dist=tmp_path)
    with TestClient(app) as client:
        assert client.get("/api/health").json()["status"] == "ok"
        response = client.get("/api/nope")
        assert response.status_code == 404 and "application/json" in response.headers["content-type"]
        assert "Test SPA" in client.get("/").text
        assert "Test SPA" in client.get("/history/123").text
        assert client.get("/asset.js").status_code == 200
        assert client.get("/vad/missing.wasm").status_code == 404
        assert client.get("/%2e%2e/requirements.txt").status_code == 404
        assert "/api/health" in client.get("/openapi.json").json()["paths"]
