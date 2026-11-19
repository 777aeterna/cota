from fastapi.testclient import TestClient
from metrilab.api import create_app

client = TestClient(create_app())


def test_parse_csv_spanish_semicolon_and_decimal_comma():
    raw = "t (s);x (m);dx (m)\n0,5;1,25;0,05\n1,0;2,50;0,05\n"
    resp = client.post("/api/data/parse-csv", json={"text": raw})
    assert resp.status_code == 200
    body = resp.json()
    assert body["headers"] == ["t (s)", "x (m)", "dx (m)"]
    assert body["rows"] == [[0.5, 1.25, 0.05], [1.0, 2.5, 0.05]]


def test_export_latex_table_with_booktabs_and_gum_rounding():
    payload = {
        "caption": "Mediciones de péndulo simple",
        "label": "tab:pendulo",
        "columns": [
            {"name": "L", "unit": "m", "values": [1.0023, 1.5012], "uncertainties": [0.0042, 0.0042]},
            {"name": "T", "unit": "s", "values": [2.0061, 2.4583], "uncertainties": [0.0148, 0.0148]},
        ],
    }
    resp = client.post("/api/data/export-latex", json=payload)
    assert resp.status_code == 200
    tex = resp.json()["latex"]
    assert r"\toprule" in tex
    assert r"\bottomrule" in tex
    assert r"1.002 \pm 0.004" in tex
    assert r"2.006 \pm 0.015" in tex
