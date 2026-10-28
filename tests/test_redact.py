from app.redact import redact


def test_redacts_properties_secrets():
    out = redact("spring.datasource.password=hunter2\nserver.port=8080\njwt.secret: abc")
    assert "hunter2" not in out and "abc" not in out
    assert "server.port=8080" in out


def test_redacts_java_literals_and_urls():
    out = redact('String apiKey = "sk-123"; url=postgres://bob:pw123@db/x')
    assert "sk-123" not in out and "pw123" not in out


def test_redacts_private_key_blocks():
    block = "-----BEGIN RSA PRIVATE KEY-----\nabc\n-----END RSA PRIVATE KEY-----"
    assert "abc" not in redact(block)
