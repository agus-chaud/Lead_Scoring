from __future__ import annotations

import json
import math
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app

PAYLOAD = json.loads(
    (Path(__file__).resolve().parent / "test_payload.json").read_text(encoding="utf-8-sig")
)
VARIABLES = {
    "origen", "fuente", "no_enviar_email", "visitas_total", "tiempo_en_site_total",
    "paginas_vistas_visita", "ult_actividad", "ambito", "ocupacion",
    "score_actividad", "score_perfil", "descarga_lm",
}

client = TestClient(app)


def test_predict_conserva_su_resultado():
    """Pins /predict: adding /explain must not change it."""
    r = client.post("/predict", json=PAYLOAD)
    assert r.status_code == 200
    fila = r.json()[0]
    assert fila["id"] == 660737
    assert fila["prediccion"] == 0
    assert fila["score"] == pytest.approx(0.15312413831374566, abs=1e-9)


def test_explain_coincide_con_predict():
    explicacion = client.post("/explain", json=PAYLOAD).json()[0]
    score = client.post("/predict", json=PAYLOAD).json()[0]["score"]

    assert explicacion["id"] == 660737
    assert explicacion["score"] == pytest.approx(score, abs=1e-9)
    assert explicacion["prediccion"] == 0


def test_los_aportes_suman_exactamente_el_logit():
    e = client.post("/explain", json=PAYLOAD).json()[0]

    logit = e["logit_referencia"] + sum(f["contribucion_logit"] for f in e["factores"])
    assert logit == pytest.approx(e["logit"], abs=1e-9)
    assert 1 / (1 + math.exp(-e["logit"])) == pytest.approx(e["score"], abs=1e-9)


def test_los_aportes_se_miden_contra_un_lead_promedio():
    """The raw logit terms are not centred: score_actividad=15 would read as +5.84 (x344)."""
    e = client.post("/explain", json=PAYLOAD).json()[0]
    por_variable = {f["variable"]: f for f in e["factores"]}

    assert 0.2 < e["score_referencia"] < 0.5
    assert e["score_referencia"] == pytest.approx(
        1 / (1 + math.exp(-e["logit_referencia"])), abs=1e-9
    )
    # A typical lead already has a high score_actividad: the real effect is modest.
    assert abs(por_variable["score_actividad"]["contribucion_logit"]) < 1.5


def test_un_dato_faltante_no_se_presenta_como_ventaja_enorme():
    e = client.post("/explain", json=[{"id": 1, "fuente": "Chat"}]).json()[0]

    assert all(abs(f["contribucion_logit"]) < 8 for f in e["factores"])
    por_variable = {f["variable"]: f for f in e["factores"]}
    assert por_variable["score_actividad"]["multiplicador_odds"] < 50


def test_hay_un_factor_por_variable_original_ordenado_por_impacto():
    e = client.post("/explain", json=PAYLOAD).json()[0]

    assert {f["variable"] for f in e["factores"]} == VARIABLES
    impactos = [abs(f["contribucion_logit"]) for f in e["factores"]]
    assert impactos == sorted(impactos, reverse=True)


def test_cada_factor_informa_valor_efecto_y_multiplicador_de_odds():
    e = client.post("/explain", json=PAYLOAD).json()[0]
    por_variable = {f["variable"]: f for f in e["factores"]}

    # 0 seconds on the site is far below a typical lead: the biggest drop.
    tiempo = por_variable["tiempo_en_site_total"]
    assert tiempo["valor"] == 0
    assert tiempo["efecto"] == "baja"
    assert tiempo["multiplicador_odds"] == pytest.approx(
        math.exp(tiempo["contribucion_logit"]), abs=1e-9
    )
    assert e["factores"][0]["variable"] == "tiempo_en_site_total"
    assert por_variable["score_actividad"]["efecto"] == "sube"
    assert por_variable["ocupacion"]["valor"] == "Unemployed"


def test_banderas_marcan_datos_faltantes_y_variables_sensibles():
    lead = {"id": 1, "fuente": "Chat", "ocupacion": "Student"}  # most fields missing
    e = client.post("/explain", json=[lead]).json()[0]

    assert set(e["banderas"]["datos_faltantes"]) == VARIABLES - {"fuente", "ocupacion"}
    assert e["banderas"]["variables_sensibles_leakage"] == ["ocupacion"]
    por_variable = {f["variable"]: f for f in e["factores"]}
    assert por_variable["score_actividad"]["valor"] is None


def test_explain_procesa_un_lote_y_respeta_el_orden():
    otro = {**PAYLOAD[0], "id": 2, "ocupacion": "Student", "tiempo_en_site_total": 900}
    r = client.post("/explain", json=[PAYLOAD[0], otro])

    assert [e["id"] for e in r.json()] == [660737, 2]


def test_explain_rechaza_los_mismos_extremos_que_predict():
    r = client.post("/explain", json=[{**PAYLOAD[0], "visitas_total": 99}])
    assert r.status_code == 422


def test_referencia_desactualizada_falla_con_mensaje_claro(tmp_path):
    from api import scoring

    ref = tmp_path / "ref.json"
    ref.write_text(json.dumps({"artefacto_sha256": "otro", "aporte_promedio": {}}), encoding="utf-8")

    with pytest.raises(RuntimeError, match="generar_referencia"):
        scoring.cargar_referencia(ref)
