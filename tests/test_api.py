from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_analyze_and_source(sample_repo):
    data = client.post("/api/analyze", json={"path": str(sample_repo)}).json()
    ep = next(e for e in data["endpoints"] if e["path"] == "/api/auth/login")
    src = client.get("/api/source", params={"path": str(sample_repo), "file": ep["file"], "line": ep["line"]})
    assert src.status_code == 200 and "login" in src.json()["snippet"]


def test_source_blocks_traversal(sample_repo):
    resp = client.get("/api/source", params={"path": str(sample_repo), "file": "../../etc/passwd", "line": 1})
    assert resp.status_code == 404


def test_source_redacts_secrets(sample_repo):
    resp = client.get(
        "/api/source",
        params={"path": str(sample_repo), "file": "src/main/resources/application.properties", "line": 3},
    )
    assert "hunter2" not in resp.text


def test_unknown_path_404():
    assert client.post("/api/analyze", json={"path": "/definitely/not/here"}).status_code == 404
    assert client.get("/api/source", params={"path": "/definitely/not/here", "file": "a", "line": 1}).status_code == 404


def test_health_without_ollama(monkeypatch):
    monkeypatch.setenv("OLLAMA_URL", "http://127.0.0.1:9")
    body = client.get("/api/health").json()
    assert body["status"] == "ok" and body["ollama"]["available"] is False


def test_report_endpoint(sample_repo):
    qa = [{"question": "q", "answer": "a", "evidence": []}]
    md = client.post("/api/report", json={"path": str(sample_repo), "qa": qa}).json()["markdown"]
    assert "### q" in md
