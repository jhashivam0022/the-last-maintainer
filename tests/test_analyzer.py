from app import analyzer, investigate, report


def test_sample_analysis(sample_repo):
    result = analyzer.analyze(str(sample_repo))
    endpoints = {(e["method"], e["path"]) for e in result["endpoints"]}
    assert ("POST", "/api/auth/login") in endpoints
    assert ("POST", "/api/auth/register") in endpoints
    assert ("GET", "/api/users/{id}") in endpoints
    assert ("GET", "/api/users/{id}/ping") in endpoints

    rels = {(r["source"], r["target"], r["kind"]) for r in result["relationships"]}
    assert ("AuthController", "AuthService", "uses") in rels
    assert ("AuthService", "UserRepository", "uses") in rels
    assert ("UserRepository", "User", "manages") in rels
    assert ("User", "Order", "relates-to") in rels

    kinds = {c["name"]: c["kind"] for c in result["components"]}
    assert kinds["UserRepository"] == "repository" and kinds["User"] == "entity"
    assert any(d["name"].endswith("spring-boot-starter-web") for d in result["repo"]["dependencies"])


def test_git_history_attached(sample_repo):
    result = analyzer.analyze(str(sample_repo))
    assert result["repo"]["is_git"]
    login = next(e for e in result["endpoints"] if e["path"] == "/api/auth/login")
    assert [c["subject"] for c in login["history"]] == ["Add register endpoint", "Initial import of legacy shop"]


def test_doc_gaps(sample_repo):
    gaps = analyzer.analyze(str(sample_repo))["doc_gaps"]
    missing = {(g["method"], g["path"]) for g in gaps["documented_not_found"]}
    assert ("POST", "/api/auth/refresh") in missing
    assert ("DELETE", "/api/users/{}") in missing
    undocumented = {(e["method"], e["path"]) for e in gaps["undocumented"]}
    assert ("POST", "/api/auth/register") in undocumented
    assert ("POST", "/api/auth/login") not in undocumented


def test_non_git_directory(tmp_path):
    (tmp_path / "README.md").write_text("hello")
    result = analyzer.analyze(str(tmp_path))
    assert not result["repo"]["is_git"]
    assert any("not a Git repository" in q for q in result["open_questions"])


def test_retrieval_and_grounded_answer(sample_repo, monkeypatch):
    analysis = analyzer.analyze(str(sample_repo))
    evidence = investigate.retrieve(analysis, "How does login work?")
    assert evidence and evidence[0]["id"] == "E1"
    assert any("login" in e["title"].lower() for e in evidence)

    monkeypatch.setattr(investigate.llm, "chat", lambda messages: "Login is handled by AuthService [E1].")
    answered = investigate.ask(analysis, "How does login work?")
    assert answered["llm_available"] and "[E1]" in answered["answer"]

    nothing = investigate.ask(analysis, "zebra quantum")
    assert nothing["answer"] is None and nothing["evidence"] == []


def test_llm_unavailable_falls_back_to_evidence(sample_repo, monkeypatch):
    analysis = analyzer.analyze(str(sample_repo))

    def boom(messages):
        raise investigate.llm.LLMUnavailable("offline")

    monkeypatch.setattr(investigate.llm, "chat", boom)
    result = investigate.ask(analysis, "login")
    assert result["answer"] is None and result["llm_available"] is False and result["evidence"]


def test_report_contents(sample_repo):
    md = report.build_report(analyzer.analyze(str(sample_repo)))
    assert "## API inventory" in md and "`/api/auth/login`" in md
    assert "## Unanswered questions" in md
    assert "hunter2" not in md
