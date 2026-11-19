from fastapi.testclient import TestClient
from metrilab.api import create_app

client = TestClient(create_app())


def test_propagation_analytical_and_monte_carlo_limits():
    payload = {
        "expression": "4 * pi**2 * L / T**2",
        "variables": {
            "L": {"value": 1.0, "uncertainty": 0.002, "distribution": "normal"},
            "T": {"value": 2.006, "uncertainty": 0.005, "distribution": "normal"},
        },
    }
    r_ana = client.post("/api/propagation/analytical", json=payload)
    assert r_ana.status_code == 200
    assert 9.7 < r_ana.json()["value"] < 9.9

    r_mc = client.post("/api/propagation/monte-carlo", json={**payload, "n_samples": 5000, "seed": 7})
    assert r_mc.status_code == 200
    assert len(r_mc.json()["histogram_counts"]) == 50

    # Límite de seguridad de Monte Carlo
    r_too_many = client.post("/api/propagation/monte-carlo", json={**payload, "n_samples": 1_000_000})
    assert r_too_many.status_code == 422

    # Expresión maliciosa -> 400
    r_bad = client.post(
        "/api/propagation/analytical",
        json={"expression": "__import__('os').system('ls')", "variables": {"x": {"value": 1, "uncertainty": 0.1}}},
    )
    assert r_bad.status_code == 400


def test_fitting_models_linear_and_nonlinear():
    r_models = client.get("/api/fitting/models")
    assert r_models.status_code == 200
    ids = {m["id"] for m in r_models.json()["models"]}
    assert {"linear", "quadratic", "exponential_decay", "gaussian"}.issubset(ids)

    r_lin = client.post(
        "/api/fitting/linear",
        json={"x": [1, 2, 3, 4, 5], "y": [3.5, 6.0, 8.5, 11.0, 13.5], "dy": [0.1] * 5},
    )
    assert r_lin.status_code == 200
    assert abs(r_lin.json()["parameters"]["m"]["value"] - 2.5) < 1e-4

    r_nl = client.post(
        "/api/fitting/nonlinear",
        json={
            "x": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
            "y": [11.5, 7.565, 5.179, 3.731, 2.853, 2.321],
            "dy": [0.05] * 6,
            "model": "exponential_decay",
        },
    )
    assert r_nl.status_code == 200
    assert abs(r_nl.json()["parameters"]["tau"]["value"] - 2.0) < 0.05
