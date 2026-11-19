from fastapi.testclient import TestClient

from cota.api import create_app

client = TestClient(create_app())


def test_root_serves_spa_and_static_assets():
    r = client.get("/")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]
    assert "Cota" in r.text
    assert client.get("/static/css/cota.css").status_code == 200
    assert client.get("/static/img/logo-cota-transparent.png").status_code == 200
    assert client.get("/static/vendor/plotly.min.js").status_code == 200
    assert client.get("/static/vendor/katex/katex.min.js").status_code == 200


def test_api_routes_still_take_precedence():
    assert client.get("/api/health").json()["status"] == "ok"
