from fastapi.testclient import TestClient
from cota.api import create_app

client = TestClient(create_app())


def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_metrology_type_a_and_combine_infinite_dof_serializes_cleanly():
    r_a = client.post("/api/metrology/type-a", json={"values": [2.01, 2.03, 1.99, 2.02, 2.00]})
    assert r_a.status_code == 200
    body_a = r_a.json()
    assert body_a["n"] == 5
    assert body_a["dof"] == 4

    # Solo Tipo B con dof=null (infinito) -> effective_dof debe serializarse como null
    r_comb = client.post(
        "/api/metrology/combine",
        json={
            "value": 9.8123,
            "components": [{"uncertainty": 0.04, "dof": None}],
            "confidence_level": 0.95,
        },
    )
    assert r_comb.status_code == 200
    assert r_comb.json()["effective_dof"] is None
    assert "±" in r_comb.json()["formatted_text"]


def test_units_convert_and_incompatible_returns_400():
    r_ok = client.post(
        "/api/units/convert",
        json={"values": [100.0, 200.0], "unit_from": "cm", "unit_to": "m", "uncertainties": [0.5, 0.5]},
    )
    assert r_ok.status_code == 200
    assert r_ok.json()["values"] == [1.0, 2.0]
    assert r_ok.json()["uncertainties"] == [0.005, 0.005]

    r_err = client.post(
        "/api/units/convert",
        json={"values": [1.0], "unit_from": "m/s", "unit_to": "kg"},
    )
    assert r_err.status_code == 400
    assert "incompatib" in r_err.json()["detail"].lower()
